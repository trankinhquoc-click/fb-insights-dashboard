import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Dashboard v5.0", page_icon="📈", layout="wide")
st.title("📈 Dashboard Phân Tích: Facebook & Instagram")

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
            return str(row[col])
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
valid_dfs = [df for df in page_dfs if 'Ngày' in df.columns]
if valid_dfs:
    merged_overview = valid_dfs[0]
    for next_df in valid_dfs[1:]: merged_overview = pd.merge(merged_overview, next_df, on="Ngày", how="outer")
    merged_overview['Ngày'] = pd.to_datetime(merged_overview['Ngày'], errors='coerce').dt.date
    merged_overview = merged_overview.dropna(subset=['Ngày']).sort_values('Ngày', ascending=False)

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

# --- 2. TẠO MENU BÊN TRÁI ---
sort_fb = None
sort_ig = None

with st.sidebar:
    st.header("🔄 Điều khiển")
    if st.button("🚀 Cập nhật dữ liệu mới"):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("---")
    st.header("⚙️ Xếp hạng báo cáo")
    st.caption("Tiêu chí bạn chọn ở đây sẽ áp dụng thẳng vào bản in PDF.")
    
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

    st.markdown("---")
    st.header("🖨️ Xuất Báo Cáo Hoàn Chỉnh")
    
    # --- 3. ĐÓNG GÓI DỮ LIỆU THÀNH HTML ĐỂ IN NGUYÊN VẸN ---
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>Báo Cáo Click Studio</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; color: #333; }
        h1 { text-align: center; color: #1877F2; margin-bottom: 30px; font-size: 24px; }
        h2 { border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-top: 40px; font-size: 18px; color: #555; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background-color: #f4f4f4; }
        @media print {
            @page { margin: 1cm; size: landscape; }
            table { page-break-inside: auto; }
            tr { page-break-inside: avoid; page-break-after: auto; }
            thead { display: table-header-group; }
        }
    </style>
    </head>
    <body onload="setTimeout(() => window.print(), 800)">
        <h1>📊 BÁO CÁO DỮ LIỆU: CLICK STUDIO</h1>
    """
    
    if merged_overview is not None and not merged_overview.empty:
        html_content += "<h2>1. TỔNG QUAN TRANG HÀNG NGÀY</h2>"
        html_content += merged_overview.to_html(index=False)
        
    if display_fb_df is not None and not display_fb_df.empty:
        html_content += f"<h2>2. HIỆU QUẢ FACEBOOK (Xếp hạng theo {sort_fb})</h2>"
        html_content += display_fb_df.to_html(index=False)
        
    if display_ig_df is not None and not display_ig_df.empty:
        html_content += f"<h2>3. HIỆU QUẢ INSTAGRAM (Xếp hạng theo {sort_ig})</h2>"
        html_content += display_ig_df.to_html(index=False)
        
    html_content += "</body></html>"
    
    st.info("💡 Bấm tải file dưới đây. Sau khi tải xong, hãy **Click mở file đó lên**. Giao diện in sẽ tự động hiện ra với toàn bộ 100% dữ liệu trải dài vô tận!")
    
    st.download_button(
        label="📥 Tải Bản In Hoàn Chỉnh",
        data=html_content,
        file_name="Bao_Cao_Click_Studio.html",
        mime="text/html",
        use_container_width=True
    )
    
    st.markdown("---")
    st.header("🔍 Trạng thái file")
    if fb_file: st.caption(f"✅ Facebook: {fb_file}")
    if ig_file: st.caption(f"✅ Instagram: {ig_file}")

# --- 4. GIAO DIỆN WEB CHÍNH THỨC ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

with tab1:
    if merged_overview is not None:
        metrics = [c for c in merged_overview.columns if c != 'Ngày']
        if metrics:
            st.subheader("Biểu đồ xu hướng")
            selected = st.multiselect("Chọn chỉ số:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
            if selected:
                fig = px.line(merged_overview.sort_values('Ngày'), x='Ngày', y=selected, markers=True)
                st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged_overview)
    else: st.warning("Chưa có dữ liệu Tổng quan.")

with tab2:
    if display_fb_df is not None and sort_fb:
        st.subheader(f"🏆 Top 10 Facebook ({sort_fb})")
        fig_fb = px.bar(display_fb_df.head(10), x=sort_fb, y=display_fb_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2'])
        fig_fb.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
        st.plotly_chart(fig_fb, use_container_width=True)
        st.dataframe(display_fb_df)
    else: st.error("Chưa tải dữ liệu Facebook lên.")

with tab3:
    if display_ig_df is not None and sort_ig:
        st.subheader(f"🏆 Top 10 Instagram ({sort_ig})")
        fig_ig = px.bar(display_ig_df.head(10), x=sort_ig, y=display_ig_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C'])
        fig_ig.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
        st.plotly_chart(fig_ig, use_container_width=True)
        st.dataframe(display_ig_df)
    else: st.error("Chưa tải dữ liệu Instagram lên.")
