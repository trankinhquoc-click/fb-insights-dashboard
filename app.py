import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Dashboard v5.6", page_icon="📈", layout="wide")

# Tiêu đề được căn giữa cho chuyên nghiệp
st.markdown("<h1 style='text-align: center;'>📈 Dashboard Phân Tích: Facebook & Instagram</h1>", unsafe_allow_html=True)

# ==========================================
# ⚙️ KHU VỰC CẤU HÌNH
# ==========================================
FB_COLS_TO_HIDE = ["Thời lượng (giây)_x", "Thời lượng (giây)_y", "Nhãn tùy chỉnh", "Trạng thái nội dung"]
IG_COLS_TO_HIDE = ["ID bài viết", "ID tài khoản", "Tên tài khoản", "Bình luận về dữ liệu"]

FB_COLUMN_ORDER = [
    "Thời gian đăng", "Nội dung hiển thị", "Số người tiếp cận", "Lượt xem",
    "Cảm xúc, bình luận và lượt chia sẻ", "Cảm xúc", "Bình luận", "Lượt chia sẻ",
    "Tổng lượt click", "Lượt click khác", "Số Giây xem", "Số Giây xem trung bình"
]

IG_COLUMN_ORDER = [
    "Thời gian đăng", "Nội dung hiển thị", "Lượt thích", "Lượt xem",
    "Số người tiếp cận", "Lượt chia sẻ", "Lượt theo dõi", "Bình luận",
    "Lượt lưu", "Thời lượng (giây)", "Loại bài viết"
]

# --- HÀM ĐỌC FILE ---
@st.cache_data
def load_csv_smart(file_path):
    for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                line1 = f.readline()
                line2 = f.readline()
            skip_n = 0
            if 'sep=' in line1.lower():
                if ',' not in line2 and '\t' not in line2: skip_n = 2
                else: skip_n = 1
            df = pd.read_csv(file_path, encoding=enc, skiprows=skip_n)
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except Exception: continue
    return None

def get_post_name(row):
    for col in ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            text = str(row[col]).strip()
            lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
            if lines:
                return lines[0]
    return "Nội dung không có tiêu đề"

def clean_numeric_df(df):
    exclude = ['ID', 'Ngày', 'Thời gian đăng', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Nội dung hiển thị']
    for col in df.columns:
        if not any(ex in col for ex in exclude) and df[col].dtype == 'object':
            try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
            except: pass
    return df

file_mapping = {
    "luot_click_vao_lien_ket.csv": "Lượt click vào liên kết", "luot_theo_doi.csv": "Lượt theo dõi",
    "luot_truy_cap.csv": "Lượt truy cập", "luot_tuong_tac.csv": "Lượt tương tác",
    "luot_xem.csv": "Lượt xem", "nguoi_xem.csv": "Người xem"
}

# --- 1. ĐỌC VÀ LÀM SẠCH DỮ LIỆU ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
fb_file = next((f for f in all_files if 'facebook' in f.lower()), None)
ig_file = next((f for f in all_files if 'insta' in f.lower() or 'ig' in f.lower()), None)

page_dfs = []
for f_name in all_files:
    f_lower = f_name.lower()
    if f_lower in file_mapping:
        df_temp = load_csv_smart(f_name)
        if df_temp is not None and not df_temp.empty:
            date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
            if date_col:
                df_temp = df_temp.rename(columns={date_col: 'Ngày'})
                metric_name = file_mapping[f_lower]
                if "Primary" in df_temp.columns:
                    page_dfs.append(df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric_name}))
                else:
                    num_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                    if num_cols: page_dfs.append(df_temp[['Ngày', num_cols[0]]].rename(columns={num_cols[0]: metric_name}))

merged_overview = None
metrics_overview = []
valid_dfs = [df for df in page_dfs if 'Ngày' in df.columns]

if valid_dfs:
    valid_dfs_agg = []
    for df in valid_dfs:
        df['Ngày'] = pd.to_datetime(df['Ngày'], errors='coerce').dt.normalize()
        df = df.dropna(subset=['Ngày'])
        
        cols = [c for c in df.columns if c != 'Ngày']
        for c in cols:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
        df_agg = df.groupby('Ngày')[cols].sum().reset_index()
        valid_dfs_agg.append(df_agg)
        
    merged_overview = valid_dfs_agg[0]
    for next_df in valid_dfs_agg[1:]: 
        merged_overview = pd.merge(merged_overview, next_df, on="Ngày", how="outer")
        
    merged_overview = merged_overview.fillna(0).sort_values('Ngày', ascending=False)
    metrics_overview = [c for c in merged_overview.columns if c != 'Ngày']

# XỬ LÝ DỮ LIỆU FACEBOOK
display_fb_df = None
if fb_file:
    fb_df = load_csv_smart(fb_file)
    if fb_df is not None:
        fb_df = clean_numeric_df(fb_df)
        fb_df['Nội dung hiển thị'] = fb_df.apply(get_post_name, axis=1)
        display_fb_df = fb_df.drop(columns=[c for c in FB_COLS_TO_HIDE if c in fb_df.columns])
        
        existing_fb = [c for c in FB_COLUMN_ORDER if c in display_fb_df.columns]
        rem_fb = [c for c in display_fb_df.columns if c not in existing_fb and c not in ['ID', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']]
        display_fb_df = display_fb_df[existing_fb + rem_fb]
        display_fb_df = display_fb_df.iloc[:, :15] 

# XỬ LÝ DỮ LIỆU INSTAGRAM
display_ig_df = None
if ig_file:
    ig_df = load_csv_smart(ig_file)
    if ig_df is not None:
        ig_df = clean_numeric_df(ig_df)
        ig_df['Nội dung hiển thị'] = ig_df.apply(get_post_name, axis=1)
        display_ig_df = ig_df.drop(columns=[c for c in IG_COLS_TO_HIDE if c in ig_df.columns])
        existing_ig = [c for c in IG_COLUMN_ORDER if c in display_ig_df.columns]
        rem_ig = [c for c in display_ig_df.columns if c not in existing_ig and c not in ['ID', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']]
        display_ig_df = display_ig_df[existing_ig + rem_ig]

# --- 2. TÍNH TOÁN THỜI GIAN & IN RA GIAO DIỆN ---
date_subtitle = ""
if merged_overview is not None and not merged_overview.empty:
    min_date = merged_overview['Ngày'].min().strftime('%d/%m/%Y')
    max_date = merged_overview['Ngày'].max().strftime('%d/%m/%Y')
    date_subtitle = f"📅 Thời gian báo cáo: {min_date} ➔ {max_date}"
    
    # Hiển thị thời gian ngay dưới tiêu đề chính
    st.markdown(f"<h4 style='text-align: center; color: #555; margin-top: -15px; padding-bottom: 20px;'>{date_subtitle}</h4>", unsafe_allow_html=True)

# --- 3. TẠO MENU BÊN TRÁI & XÂY DỰNG BIỂU ĐỒ ---
sort_fb = None
sort_ig = None

with st.sidebar:
    st.header("🔄 Điều khiển")
    if st.button("🚀 Cập nhật dữ liệu mới"):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("---")
    st.header("⚙️ Xếp hạng báo cáo")
    st.caption("Chọn chỉ số để biểu đồ vẽ theo:")
    
    selected_overview = st.multiselect("Chỉ số Tổng quan:", metrics_overview, default=metrics_overview[:2] if len(metrics_overview)>1 else metrics_overview) if metrics_overview else []
    
    if display_fb_df is not None:
        num_cols_fb = [c for c in display_fb_df.columns if display_fb_df[c].dtype in ['float64', 'int64']]
        if num_cols_fb:
            sort_fb = st.selectbox("Facebook theo:", num_cols_fb, key="sb_fb")
            display_fb_df = display_fb_df.sort_values(sort_fb, ascending=False)
            
    if display_ig_df is not None:
        num_cols_ig = [c for c in display_ig_df.columns if display_ig_df[c].dtype in ['float64', 'int64']]
        if num_cols_ig:
            sort_ig = st.selectbox("Instagram theo:", num_cols_ig, key="sb_ig")
            display_ig_df = display_ig_df.sort_values(sort_ig, ascending=False)

fig_overview = None
if merged_overview is not None and selected_overview:
    df_chart = merged_overview.sort_values('Ngày', ascending=True)
    fig_overview = px.line(df_chart, x='Ngày', y=selected_overview, markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
    fig_overview.update_xaxes(type='date', title='Thời gian')

fig_fb = px.bar(display_fb_df.head(10), x=sort_fb, y=display_fb_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2']).update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}) if display_fb_df is not None and sort_fb else None
fig_ig = px.bar(display_ig_df.head(10), x=sort_ig, y=display_ig_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C']).update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}) if display_ig_df is not None and sort_ig else None

with st.sidebar:
    st.markdown("---")
    st.header("🖨️ Xuất Báo Cáo PDF")
    
    # --- 4. ĐÓNG GÓI DỮ LIỆU + THỜI GIAN VÀO PDF ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>Báo Cáo Click Studio</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f2f5; }}
        #report-container {{ background: white; padding: 40px; border-radius: 10px; max-width: 1200px; margin: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #1877F2; margin-bottom: 10px; font-size: 28px; text-transform: uppercase; }}
        .date-subtitle {{ text-align: center; color: #666; font-size: 16px; margin-top: 0; margin-bottom: 40px; font-weight: bold; }}
        h2 {{ border-bottom: 2px solid #1877F2; padding-bottom: 8px; margin-top: 50px; font-size: 20px; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; font-size: 12px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f8f9fa; color: #333; }}
        
        #download-btn {{
            position: fixed; top: 20px; right: 20px; padding: 15px 25px; 
            background: linear-gradient(135deg, #FF4B4B, #E1306C); color: white; 
            border: none; border-radius: 8px; font-size: 16px; font-weight: bold; 
            cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.2); z-index: 9999;
            transition: transform 0.2s;
        }}
        #download-btn:hover {{ transform: scale(1.05); }}

        @media print {{
            body {{ background-color: white; padding: 0; }}
            #report-container {{ box-shadow: none; max-width: 100%; padding: 0; margin: 0; }}
            #download-btn {{ display: none !important; }} 
            table {{ page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}
            thead {{ display: table-header-group; }}
            h2 {{ page-break-after: avoid; }}
            .plotly-graph-div {{ page-break-inside: avoid; margin-bottom: 20px; }}
        }}
    </style>
    </head>
    <body>
        <button id="download-btn" onclick="window.print()">📄 LƯU BÁO CÁO THÀNH PDF</button>
        <div id="report-container">
            <h1>📊 BÁO CÁO DỮ LIỆU: CLICK STUDIO</h1>
            <p class="date-subtitle">{date_subtitle}</p>
    """
    
    if merged_overview is not None:
        html_content += "<h2>1. TỔNG QUAN TRANG HÀNG NGÀY</h2>"
        if fig_overview: html_content += fig_overview.to_html(full_html=False, include_plotlyjs=False)
        
        df_export = merged_overview.copy()
        df_export['Ngày'] = df_export['Ngày'].dt.strftime('%d/%m/%Y')
        html_content += df_export.to_html(index=False)
        
    if display_fb_df is not None:
        html_content += f"<h2>2. HIỆU QUẢ FACEBOOK (Xếp hạng theo {sort_fb})</h2>"
        if fig_fb: html_content += fig_fb.to_html(full_html=False, include_plotlyjs=False)
        html_content += display_fb_df.head(20).to_html(index=False)
        
    if display_ig_df is not None:
        html_content += f"<h2>3. HIỆU QUẢ INSTAGRAM (Xếp hạng theo {sort_ig})</h2>"
        if fig_ig: html_content += fig_ig.to_html(full_html=False, include_plotlyjs=False)
        html_content += display_ig_df.head(20).to_html(index=False)
        
    html_content += """
        </div>
    </body>
    </html>
    """
    
    st.info("💡 Bấm tải file dưới đây. Mở file HTML vừa tải lên => Bấm nút **Lưu Báo Cáo Thành PDF** màu đỏ ở góc phải.")
    
    st.download_button(
        label="📥 Tải Bản Báo Cáo Kèm Đồ Thị",
        data=html_content,
        file_name="Bao_Cao_Click_Studio.html",
        mime="text/html",
        use_container_width=True
    )
    
    st.markdown("---")
    st.header("🔍 Trạng thái file")
    if fb_file: st.caption(f"✅ Facebook: {fb_file}")
    if ig_file: st.caption(f"✅ Instagram: {ig_file}")

# --- 5. GIAO DIỆN WEB CHÍNH THỨC ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

with tab1:
    if merged_overview is not None:
        st_df = merged_overview.copy()
        st_df['Ngày'] = st_df['Ngày'].dt.strftime('%d/%m/%Y')
        
        if fig_overview: st.plotly_chart(fig_overview, use_container_width=True)
        st.dataframe(st_df)
    else: st.warning("Chưa có dữ liệu Tổng quan.")

with tab2:
    if display_fb_df is not None and sort_fb:
        if fig_fb: st.plotly_chart(fig_fb, use_container_width=True)
        st.dataframe(display_fb_df)
    else: st.error("Chưa tải dữ liệu Facebook lên.")

with tab3:
    if display_ig_df is not None and sort_ig:
        if fig_ig: st.plotly_chart(fig_ig, use_container_width=True)
        st.dataframe(display_ig_df)
    else: st.error("Chưa tải dữ liệu Instagram lên.")
