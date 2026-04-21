import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Dashboard v4.9", page_icon="📈", layout="wide")
st.title("📈 Dashboard Phân Tích: Facebook & Instagram")

# ==========================================
# 🖨️ CSS CHUYÊN DỤNG CHO BẢN IN
# ==========================================
st.markdown("""
<style>
.print-table {
    width: 100%; border-collapse: collapse; font-size: 13px; font-family: sans-serif;
}
.print-table th, .print-table td {
    border: 1px solid #ddd; padding: 6px; text-align: left;
}
.print-table th { background-color: #f2f2f2; }

@media print {
    /* Ép tất cả các thẻ div trải dài ra, không được cuộn */
    html, body, .stApp, .main, div, section {
        height: auto !important; max-height: none !important; overflow: visible !important;
    }
    /* Giấu menu và thanh công cụ */
    [data-testid="stSidebar"], header, [data-testid="stToolbar"] { display: none !important; }
    /* Giữ bảng không bị cắt ngang dòng */
    table { page-break-inside: auto; }
    tr { page-break-inside: avoid; page-break-after: auto; }
}
</style>
""", unsafe_allow_html=True)

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

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔄 Điều khiển")
    if st.button("🚀 Bấm để cập nhật dữ liệu"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.header("🖨️ Xuất Báo Cáo PDF")
    # CÔNG TẮC GỘP TAB
    print_mode = st.checkbox("✅ Bật Chế độ in PDF (Gộp Tab)", value=False)
    st.info("💡 Bật công tắc này, đợi giao diện chuyển sang dạng cuộn dài rồi nhấn Cmd+P / Ctrl+P.")

    st.markdown("---")
    st.header("🔍 Trạng thái file")
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    fb_file = next((f for f in all_files if 'facebook' in f.lower()), None)
    ig_file = next((f for f in all_files if 'insta' in f.lower() or 'ig' in f.lower()), None)
    if fb_file: st.caption(f"✅ Facebook: {fb_file}")
    if ig_file: st.caption(f"✅ Instagram: {ig_file}")

# --- TIỀN XỬ LÝ DỮ LIỆU ---
page_dfs = []
fb_df = load_csv_smart(fb_file) if fb_file else None
ig_df = load_csv_smart(ig_file) if ig_file else None

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

# Xử lý Data Tổng quan
merged_overview = None
metrics_overview = []
valid_dfs = [df for df in page_dfs if 'Ngày' in df.columns]
if valid_dfs:
    merged_overview = valid_dfs[0]
    for next_df in valid_dfs[1:]: merged_overview = pd.merge(merged_overview, next_df, on="Ngày", how="outer")
    merged_overview['Ngày'] = pd.to_datetime(merged_overview['Ngày'], errors='coerce').dt.date
    merged_overview = merged_overview.dropna(subset=['Ngày']).sort_values('Ngày', ascending=False)
    metrics_overview = [c for c in merged_overview.columns if c != 'Ngày']

# Xử lý Data FB
display_fb_df = None
sort_fb_options = []
if fb_df is not None:
    fb_df = clean_numeric_df(fb_df)
    fb_df['Nội dung hiển thị'] = fb_df.apply(get_post_name, axis=1)
    display_fb_df = fb_df.drop(columns=[c for c in FB_COLS_TO_HIDE if c in fb_df.columns])
    existing_fb = [c for c in FB_COLUMN_ORDER if c in display_fb_df.columns]
    rem_fb = [c for c in display_fb_df.columns if c not in existing_fb and c not in ['ID', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']]
    display_fb_df = display_fb_df[existing_fb + rem_fb]
    sort_fb_options = [c for c in display_fb_df.columns if display_fb_df[c].dtype in ['float64', 'int64']]

# Xử lý Data IG
display_ig_df = None
sort_ig_options = []
if ig_df is not None:
    ig_df = clean_numeric_df(ig_df)
    ig_df['Nội dung hiển thị'] = ig_df.apply(get_post_name, axis=1)
    display_ig_df = ig_df.drop(columns=[c for c in IG_COLS_TO_HIDE if c in ig_df.columns])
    existing_ig = [c for c in IG_COLUMN_ORDER if c in display_ig_df.columns]
    rem_ig = [c for c in display_ig_df.columns if c not in existing_ig and c not in ['ID', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']]
    display_ig_df = display_ig_df[existing_ig + rem_ig]
    sort_ig_options = [c for c in display_ig_df.columns if display_ig_df[c].dtype in ['float64', 'int64']]

# ==========================================
# HÀM RENDER UI CHUNG
# ==========================================
def render_overview_section(is_print):
    if merged_overview is not None and metrics_overview:
        selected = st.multiselect("Chọn chỉ số:", metrics_overview, default=metrics_overview[:2] if len(metrics_overview)>1 else metrics_overview)
        if selected:
            fig = px.line(merged_overview.sort_values('Ngày'), x='Ngày', y=selected, markers=True)
            st.plotly_chart(fig, use_container_width=True)
        if is_print: st.markdown(merged_overview.to_html(index=False, classes="print-table"), unsafe_allow_html=True)
        else: st.dataframe(merged_overview)
    else: st.warning("Chưa có dữ liệu Tổng quan.")

def render_fb_section(is_print):
    if display_fb_df is not None and sort_fb_options:
        sort_fb = st.selectbox("Sắp xếp Facebook theo:", sort_fb_options, key="sb_fb")
        df_sorted = display_fb_df.sort_values(sort_fb, ascending=False)
        st.subheader(f"🏆 Top 10 Facebook ({sort_fb})")
        fig_fb = px.bar(df_sorted.head(10), x=sort_fb, y=df_sorted.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2'])
        fig_fb.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
        st.plotly_chart(fig_fb, use_container_width=True)
        if is_print: st.markdown(df_sorted.to_html(index=False, classes="print-table"), unsafe_allow_html=True)
        else: st.dataframe(df_sorted)
    else: st.error("Chưa tải dữ liệu Facebook lên.")

def render_ig_section(is_print):
    if display_ig_df is not None and sort_ig_options:
        sort_ig = st.selectbox("Sắp xếp Instagram theo:", sort_ig_options, key="sb_ig")
        df_sorted = display_ig_df.sort_values(sort_ig, ascending=False)
        st.subheader(f"🏆 Top 10 Instagram ({sort_ig})")
        fig_ig = px.bar(df_sorted.head(10), x=sort_ig, y=df_sorted.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C'])
        fig_ig.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
        st.plotly_chart(fig_ig, use_container_width=True)
        if is_print: st.markdown(df_sorted.to_html(index=False, classes="print-table"), unsafe_allow_html=True)
        else: st.dataframe(df_sorted)
    else: st.error("Chưa tải dữ liệu Instagram lên.")

# ==========================================
# ĐIỀU HƯỚNG GIAO DIỆN DỰA VÀO CHẾ ĐỘ IN
# ==========================================
if print_mode:
    st.success("🖨️ **Chế độ In đang bật:** Các Tab đã được gỡ bỏ. Dữ liệu đang được trải dài từ trên xuống dưới. Hãy nhấn **Cmd+P** hoặc **Ctrl+P** ngay bây giờ để lưu toàn bộ số liệu.")
    
    st.markdown("## 📊 1. Tổng quan Trang")
    render_overview_section(True)
    
    st.markdown("---")
    st.markdown("## 📘 2. Hiệu quả Facebook")
    render_fb_section(True)
    
    st.markdown("---")
    st.markdown("## 📸 3. Hiệu quả Instagram")
    render_ig_section(True)
    
else:
    tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])
    with tab1: render_overview_section(False)
    with tab2: render_fb_section(False)
    with tab3: render_ig_section(False)
