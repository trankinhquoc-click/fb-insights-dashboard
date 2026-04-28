import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Dashboard v6.0", page_icon="📈", layout="wide")
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

# TỪ KHÓA NHẬN DIỆN CÁC FILE TỔNG QUAN
overview_keywords = {
    "luot_click": "Lượt click",
    "luot_theo_doi": "Lượt theo dõi",
    "luot_truy_cap": "Lượt truy cập",
    "luot_tuong_tac": "Lượt tương tác",
    "luot_xem": "Lượt xem",
    "nguoi_xem": "Người xem",
    "so_nguoi_tiep_can": "Số người tiếp cận"
}

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

def merge_overview_dfs(dfs):
    if not dfs: return None, []
    valid_dfs_agg = []
    for df in dfs:
        df['Ngày'] = pd.to_datetime(df['Ngày'], errors='coerce').dt.normalize()
        df = df.dropna(subset=['Ngày'])
        cols = [c for c in df.columns if c != 'Ngày']
        for c in cols:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        df_agg = df.groupby('Ngày')[cols].sum().reset_index()
        valid_dfs_agg.append(df_agg)
        
    merged = valid_dfs_agg[0]
    for next_df in valid_dfs_agg[1:]: 
        merged = pd.merge(merged, next_df, on="Ngày", how="outer")
    merged = merged.fillna(0).sort_values('Ngày', ascending=False)
    metrics = [c for c in merged.columns if c != 'Ngày']
    return merged, metrics

# --- 1. ĐỌC VÀ LÀM SẠCH DỮ LIỆU ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
fb_file = next((f for f in all_files if 'facebook' in f.lower()), None)
ig_file = next((f for f in all_files if 'insta' in f.lower() or 'ig' in f.lower()), None)

fb_page_dfs = []
ig_page_dfs = []

# Tự động phân loại file Tổng quan
for f_name in all_files:
    f_lower = f_name.lower()
    if f_lower in ['facebook.csv', 'insta.csv']: continue
    
    metric_name = None
    for key, display_name in overview_keywords.items():
        if key in f_lower:
            metric_name = display_name
            break
            
    if metric_name:
        df_temp = load_csv_smart(f_name)
        if df_temp is not None and not df_temp.empty:
            date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
            if date_col:
                df_temp = df_temp.rename(columns={date_col: 'Ngày'})
                if "Primary" in df_temp.columns:
                    df_target = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric_name})
                else:
                    num_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                    if num_cols: df_target = df_temp[['Ngày', num_cols[0]]].rename(columns={num_cols[0]: metric_name})
                    else: df_target = None
                    
                if df_target is not None:
                    # TRÍ TUỆ NHÂN TẠO: Phân biệt IG hay FB
                    is_ig = False
                    if f_lower.startswith('ig_') or f_lower.startswith('insta_'):
                        is_ig = True
                    elif f_lower.startswith('fb_') or f_lower.startswith('face_'):
                        is_ig = False
                    else:
                        # Đọc lướt nội dung file xem có chữ instagram không
                        for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
                            try:
                                with open(f_name, 'r', encoding=enc) as f:
                                    if 'instagram' in f.read(200).lower():
                                        is_ig = True
                                        break
                            except: pass
                            
                    if is_ig: ig_page_dfs.append(df_target)
                    else: fb_page_dfs.append(df_target)

# Gộp dữ liệu Tổng quan thành 2 luồng độc lập
merged_fb_overview, metrics_fb_overview = merge_overview_dfs(fb_page_dfs)
merged_ig_overview, metrics_ig_overview = merge_overview_dfs(ig_page_dfs)

# XỬ LÝ DỮ LIỆU BÀI VIẾT FACEBOOK
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

# XỬ LÝ DỮ LIỆU BÀI VIẾT INSTAGRAM
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

# --- 2. TÍNH TOÁN THỜI GIAN CHUNG ---
min_dates, max_dates = [], []
if merged_fb_overview is not None:
    min_dates.append(merged_fb_overview['Ngày'].min())
    max_dates.append(merged_fb_overview['Ngày'].max())
if merged_ig_overview is not None:
    min_dates.append(merged_ig_overview['Ngày'].min())
    max_dates.append(merged_ig_overview['Ngày'].max())

date_subtitle = ""
if min_dates and max_dates:
    min_date = min(min_dates).strftime('%d/%m/%Y')
    max_date = max(max_dates).strftime('%d/%m/%Y')
    date_subtitle = f"📅 Thời gian báo cáo: {min_date} ➔ {max_date}"
    st.markdown(f"<h4 style='text-align: center; color: #555; margin-top: -15px; padding-bottom: 20px;'>{date_subtitle}</h4>", unsafe_allow_html=True)

# --- 3. TẠO MENU BÊN TRÁI & BIỂU ĐỒ ---
sort_fb = None
sort_ig = None

with st.sidebar:
    st.header("🔄 Điều khiển")
    if st.button("🚀 Cập nhật dữ liệu mới"):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("---")
    st.header("⚙️ Xếp hạng & Chỉ số")
    
    selected_fb_overview = st.multiselect("Chỉ số T.Quan Facebook:", metrics_fb_overview, default=metrics_fb_overview[:2] if len(metrics_fb_overview)>1 else metrics_fb_overview) if metrics_fb_overview else []
    selected_ig_overview = st.multiselect("Chỉ số T.Quan Instagram:", metrics_ig_overview, default=metrics_ig_overview[:2] if len(metrics_ig_overview)>1 else metrics_ig_overview) if metrics_ig_overview else []
    
    if display_fb_df is not None:
        num_cols_fb = [c for c in display_fb_df.columns if display_fb_df[c].dtype in ['float64', 'int64']]
        if num_cols_fb:
            sort_fb = st.selectbox("Xếp hạng bài viết FB theo:", num_cols_fb, key="sb_fb")
            display_fb_df = display_fb_df.sort_values(sort_fb, ascending=False)
            
    if display_ig_df is not None:
        num_cols_ig = [c for c in display_ig_df.columns if display_ig_df[c].dtype in ['float64', 'int64']]
        if num_cols_ig:
            sort_ig = st.selectbox("Xếp hạng bài viết IG theo:", num_cols_ig, key="sb_ig")
            display_ig_df = display_ig_df.sort_values(sort_ig, ascending=False)

fig_fb_overview = None
if merged_fb_overview is not None and selected_fb_overview:
    df_chart = merged_fb_overview.sort_values('Ngày', ascending=True)
    fig_fb_overview = px.line(df_chart, x='Ngày', y=selected_fb_overview, markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
    fig_fb_overview.update_xaxes(type='date', title='Thời gian')

fig_ig_overview = None
if merged_ig_overview is not None and selected_ig_overview:
    df_chart = merged_ig_overview.sort_values('Ngày', ascending=True)
    fig_ig_overview = px.line(df_chart, x='Ngày', y=selected_ig_overview, markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
    fig_ig_overview.update_xaxes(type='date', title='Thời gian')

fig_fb = px.bar(display_fb_df.head(10), x=sort_fb, y=display_fb_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2']).update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}) if display_fb_df is not None and sort_fb else None
fig_ig = px.bar(display_ig_df.head(10), x=sort_ig, y=display_ig_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C']).update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}) if display_ig_df is not None and sort_ig else None

with st.sidebar:
    st.markdown("---")
    st.header("🖨️ Xuất Báo Cáo PDF Chuyên Nghiệp")
    
    # --- 4. TÍCH HỢP HỆ THỐNG XUẤT PDF TRỰC TIẾP ---
    if st.button("📥 TẢI XUỐNG FILE PDF", type="primary", use_container_width=True):
        st.info("⏳ Đang kết xuất PDF, vui lòng chờ khoảng 3 giây. File sẽ tự động tải xuống!")
        
        pdf_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: white; margin: 0; padding: 0; }}
            #msg-box {{ padding: 10px; background: #28a745; color: white; text-align: center; font-weight: bold; font-family: sans-serif; border-radius: 5px; }}
            #report-container {{ width: 1100px; padding: 20px; }}
            h1 {{ text-align: center; color: #1877F2; font-size: 26px; text-transform: uppercase; margin-bottom: 5px; }}
            .date-subtitle {{ text-align: center; color: #666; font-size: 14px; margin-bottom: 30px; font-weight: bold; }}
            h2 {{ border-bottom: 2px solid #1877F2; padding-bottom: 5px; margin-top: 40px; font-size: 18px; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; font-size: 11px; }}
            th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
            th {{ background-color: #f4f4f4; color: #333; }}
        </style>
        </head>
        <body>
            <div id="msg-box">Hệ thống đang xử lý cấu trúc báo cáo...</div>
            <div id="report-container">
                <h1>📊 BÁO CÁO DỮ LIỆU: CLICK STUDIO</h1>
                <p class="date-subtitle">{date_subtitle}</p>
        """
        
        section_idx = 1
        
        if merged_fb_overview is not None:
            pdf_html += f"<h2>{section_idx}. TỔNG QUAN FACEBOOK HÀNG NGÀY</h2>"
            if fig_fb_overview: pdf_html += fig_fb_overview.to_html(full_html=False, include_plotlyjs=False)
            df_export = merged_fb_overview.copy()
            df_export['Ngày'] = df_export['Ngày'].dt.strftime('%d/%m/%Y')
            pdf_html += df_export.to_html(index=False)
            section_idx += 1
            
        if merged_ig_overview is not None:
            pdf_html += f"<h2>{section_idx}. TỔNG QUAN INSTAGRAM HÀNG NGÀY</h2>"
            if fig_ig_overview: pdf_html += fig_ig_overview.to_html(full_html=False, include_plotlyjs=False)
            df_export = merged_ig_overview.copy()
            df_export['Ngày'] = df_export['Ngày'].dt.strftime('%d/%m/%Y')
            pdf_html += df_export.to_html(index=False)
            section_idx += 1
            
        if display_fb_df is not None:
            pdf_html += f"<h2>{section_idx}. HIỆU QUẢ FACEBOOK (Xếp hạng theo {sort_fb})</h2>"
            if fig_fb: pdf_html += fig_fb.to_html(full_html=False, include_plotlyjs=False)
            pdf_html += display_fb_df.head(20).to_html(index=False)
            section_idx += 1
            
        if display_ig_df is not None:
            pdf_html += f"<h2>{section_idx}. HIỆU QUẢ INSTAGRAM (Xếp hạng theo {sort_ig})</h2>"
            if fig_ig: pdf_html += fig_ig.to_html(full_html=False, include_plotlyjs=False)
            pdf_html += display_ig_df.head(20).to_html(index=False)
            
        pdf_html += """
            </div>
            <script>
                setTimeout(() => {
                    var element = document.getElementById('report-container');
                    var opt = {
                        margin:       0.4,
                        filename:     'Bao_Cao_Click_Studio.pdf',
                        image:        { type: 'jpeg', quality: 0.98 },
                        html2canvas:  { scale: 2, useCORS: true, logging: false },
                        jsPDF:        { unit: 'in', format: 'a4', orientation: 'landscape' }
                    };
                    html2pdf().set(opt).from(element).save().then(() => {
                        document.getElementById('msg-box').innerText = "✅ Đã tải xong PDF! Kiểm tra thư mục Download của bạn.";
                    });
                }, 2500);
            </script>
        </body>
        </html>
        """
        
        components.html(pdf_html, height=120, scrolling=True)

    st.markdown("---")
    st.header("🔍 Trạng thái file")
    if fb_file: st.caption(f"✅ Bài viết FB: {fb_file}")
    if ig_file: st.caption(f"✅ Bài viết IG: {ig_file}")
    st.caption(f"✅ T.Quan FB: {len(fb_page_dfs)} file")
    st.caption(f"✅ T.Quan IG: {len(ig_page_dfs)} file")

# --- 5. GIAO DIỆN WEB CHÍNH THỨC (4 TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng quan FB", "📸 Tổng quan IG", "📘 Bài viết FB", "📸 Bài viết IG"])

with tab1:
    if merged_fb_overview is not None:
        st_df = merged_fb_overview.copy()
        st_df['Ngày'] = st_df['Ngày'].dt.strftime('%d/%m/%Y')
        if fig_fb_overview: st.plotly_chart(fig_fb_overview, use_container_width=True)
        st.dataframe(st_df)
    else: st.warning("Chưa có dữ liệu Tổng quan Facebook.")

with tab2:
    if merged_ig_overview is not None:
        st_df = merged_ig_overview.copy()
        st_df['Ngày'] = st_df['Ngày'].dt.strftime('%d/%m/%Y')
        if fig_ig_overview: st.plotly_chart(fig_ig_overview, use_container_width=True)
        st.dataframe(st_df)
    else: st.warning("Chưa có dữ liệu Tổng quan Instagram.")

with tab3:
    if display_fb_df is not None and sort_fb:
        if fig_fb: st.plotly_chart(fig_fb, use_container_width=True)
        st.dataframe(display_fb_df)
    else: st.error("Chưa tải dữ liệu Bài viết Facebook lên.")

with tab4:
    if display_ig_df is not None and sort_ig:
        if fig_ig: st.plotly_chart(fig_ig, use_container_width=True)
        st.dataframe(display_ig_df)
    else: st.error("Chưa tải dữ liệu Bài viết Instagram lên.")
