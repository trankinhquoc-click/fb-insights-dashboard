import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Đa Nền Tảng", page_icon="🚀", layout="wide")
st.title("🚀 Dashboard Phân Tích: Facebook & Instagram")

# --- HÀM ĐỌC FILE THÔNG MINH ---
@st.cache_data
def load_csv_smart(file_content, is_path=True):
    try:
        if is_path:
            with open(file_content, 'rb') as f:
                content = f.read()
        else:
            content = file_content.read() # Dành cho file tải lên qua web
            
        try:
            text = content.decode('utf-16')
        except UnicodeError:
            text = content.decode('utf-8')
        
        lines = text.splitlines()
        if len(lines) > 0 and 'sep=,' in lines[0]:
            lines = lines[2:]
            
        text = '\n'.join(lines)
        return pd.read_csv(io.StringIO(text))
    except Exception as e:
        return None

# --- HÀM TÌM TÊN BÀI VIẾT ---
def get_post_name(row):
    for col in ["Tiêu đề", "Mô tả", "Nội dung"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
            
    if "Liên kết vĩnh viễn" in row.index and pd.notna(row["Liên kết vĩnh viễn"]):
        link_str = str(row["Liên kết vĩnh viễn"])
        if "/" in link_str:
            return "Bài đăng: " + link_str.split("/")[-2]
        return link_str
    return "Nội dung không có tiêu đề"

# --- KHU VỰC ĐIỀU KHIỂN & BẢO HIỂM LỖI (BÊN TRÁI) ---
with st.sidebar:
    st.header("⚙️ Bảng Điều Khiển")
    
    # Khu vực soi lỗi hệ thống
    sys_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    st.write("📁 **File hệ thống tự động tìm thấy:**")
    if sys_files:
        for f in sys_files: 
            st.caption(f"✅ {f}")
    else:
        st.caption("❌ Trống (Vui lòng upload lên GitHub)")
        
    st.markdown("---")
    st.info("💡 Nếu thiếu file ở trên, bạn có thể tải bù vào ô bên dưới để xem ngay lập tức:")
    extra_files = st.file_uploader("Tải thêm file CSV bằng tay", accept_multiple_files=True, type=['csv'])

# --- GOM VÀ PHÂN LOẠI DỮ LIỆU ---
page_dfs, fb_post_dfs, ig_post_dfs = [], [], []

def classify_data(df_temp, f_name):
    if df_temp is not None and not df_temp.empty:
        f_lower = f_name.lower()
        # Phân loại Tab 1
        if "Primary" in df_temp.columns or ("Lượt tương tác của người dùng" in df_temp.columns and "ID bài viết" not in df_temp.columns):
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            page_dfs.append(df_temp)
        # Phân loại Tab FB / IG
        else:
            if 'insta' in f_lower or 'ig' in f_lower:
                ig_post_dfs.append(df_temp)
            else:
                fb_post_dfs.append(df_temp)

# 1. Xử lý file tự động từ GitHub
for f_name in sys_files:
    classify_data(load_csv_smart(f_name, is_path=True), f_name)

# 2. Xử lý file do người dùng tự tải thêm qua giao diện
if extra_files:
    for file in extra_files:
        classify_data(load_csv_smart(file, is_path=False), file.name)

# --- HÀM VẼ GIAO DIỆN BÀI VIẾT ---
def render_post_tab(dfs_list, platform_name, chart_color):
    if dfs_list:
        final_df = pd.concat(dfs_list, ignore_index=True)
        final_df['Tên hiển thị'] = final_df.apply(get_post_name, axis=1)
        final_df['Tên hiển thị'] = final_df['Tên hiển thị'].apply(lambda x: x[:70] + "..." if len(x) > 70 else x)

        # Ép các cột số liệu về dạng số chuẩn (phòng trường hợp FB xuất số có dấu phẩy 1,000)
        exclude_cols = ['ID Trang', 'ID bài viết', 'ID tài sản video', 'ID video chung', 'ID tài khoản', 'Tổng lượt click', 'Lượt click khác']
        for col in final_df.columns:
            if col not in exclude_cols and col not in ['Tên hiển thị', 'Thời gian đăng', 'Ngày', 'Liên kết vĩnh viễn']:
                try:
                    final_df[col] = pd.to_numeric(final_df[col].astype(str).str.replace(',', ''), errors='ignore')
                except:
                    pass

        num_cols = final_df.select_dtypes(include=['number']).columns.tolist()
        num_cols = [c for c in num_cols if c not in exclude_cols]
        
        if num_cols:
            col_filter, _ = st.columns([1, 2])
            with col_filter:
                sort_m = st.selectbox(f"Xếp hạng theo chỉ số ({platform_name}):", num_cols, key=f"sort_{platform_name}")
            
            final_df = final_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 nội dung {platform_name} cao nhất")
            fig = px.bar(final_df.head(10), x=sort_m, y='Tên hiển thị', orientation='h', text_auto=True, color_discrete_sequence=[chart_color])
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Bảng dữ liệu chi tiết")
            st.dataframe(final_df)
        else:
            st.warning("Không tìm thấy cột số liệu để vẽ biểu đồ.")
            st.dataframe(final_df)
    else:
        st.info(f"Chưa có dữ liệu. Vui lòng tải file chứa chữ '{platform_name}' vào thanh bên trái.")

# --- GIAO DIỆN 3 TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

with tab1:
    if page_dfs:
        merged = page_dfs[0]
        for next_df in page_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        merged['Ngày'] = pd.to_datetime(merged['Ngày']).dt.date
        metrics = [c for c in merged.columns if c != 'Ngày']
        
        col_filter, _ = st.columns([1, 2])
        with col_filter:
            sort_p = st.selectbox("Sắp xếp bảng dữ liệu theo:", ["Ngày"] + metrics, key="sort_page")
            
        merged = merged.sort_values(sort_p, ascending=False)

        st.subheader("Biểu đồ xu hướng")
        selected = st.multiselect("Chọn chỉ số để xem biểu đồ:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
        if selected:
            fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected, markers=True, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged)
    else:
        st.warning("Chưa có dữ liệu Tổng quan Trang.")

with tab2:
    render_post_tab(fb_post_dfs, "Facebook", "#1877F2")

with tab3:
    render_post_tab(ig_post_dfs, "Insta", "#E1306C")
