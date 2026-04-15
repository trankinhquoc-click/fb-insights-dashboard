import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Đa Nền Tảng", page_icon="🚀", layout="wide")
st.title("🚀 Dashboard Phân Tích: Facebook & Instagram")

# --- HÀM ĐỌC FILE SIÊU CHUẨN (KHẮC PHỤC LỖI MẤT HEADER) ---
@st.cache_data
def load_csv_smart(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Nhận diện chuẩn mã hóa
        try:
            text = content.decode('utf-16')
        except UnicodeError:
            text = content.decode('utf-8')
        
        # Chỉ cắt 2 dòng đầu NẾU thực sự có dòng rác 'sep=,'
        lines = text.splitlines()
        if len(lines) > 0 and 'sep=,' in lines[0]:
            lines = lines[2:]
            
        text = '\n'.join(lines)
        return pd.read_csv(io.StringIO(text))
    except Exception as e:
        return None

# --- QUÉT VÀ PHÂN LOẠI FILE TỰ ĐỘNG ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
page_dfs = []
fb_post_dfs = []
ig_post_dfs = []

for f_name in all_files:
    df_temp = load_csv_smart(f_name)
    if df_temp is not None and not df_temp.empty:
        f_lower = f_name.lower()
        
        # Phân loại Tab 1 (Tổng quan)
        if "Primary" in df_temp.columns or ("Lượt tương tác của người dùng" in df_temp.columns and "ID bài viết" not in df_temp.columns):
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            page_dfs.append(df_temp)
            
        # Phân loại Tab 2 & 3 (Bài viết FB / IG)
        else:
            if 'insta' in f_lower or 'ig' in f_lower:
                ig_post_dfs.append(df_temp)
            else:
                fb_post_dfs.append(df_temp)

# --- HÀM TÌM TÊN BÀI VIẾT THÔNG MINH (KHẮC PHỤC LỖI SỐ RANDOM) ---
def get_post_name(row):
    # Quét từng cột, cái nào có chữ thì lấy làm tên hiển thị
    for col in ["Tiêu đề", "Mô tả", "Nội dung"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
            
    # Nếu nội dung trống trơn (như video không tiêu đề), lấy Link để làm tên
    if "Liên kết vĩnh viễn" in row.index and pd.notna(row["Liên kết vĩnh viễn"]):
        link_str = str(row["Liên kết vĩnh viễn"])
        if "/" in link_str:
            return "Bài đăng: " + link_str.split("/")[-2]
        return link_str
        
    return "Video/Bài viết không có tiêu đề"

def render_post_tab(dfs_list, platform_name, chart_color):
    if dfs_list:
        final_df = pd.concat(dfs_list, ignore_index=True)
        
        # Áp dụng hàm tìm tên thông minh cho từng bài viết
        final_df['Tên hiển thị'] = final_df.apply(get_post_name, axis=1)
        # Cắt ngắn nếu tên quá dài (giúp biểu đồ không bị vỡ)
        final_df['Tên hiển thị'] = final_df['Tên hiển thị'].apply(lambda x: x[:70] + "..." if len(x) > 70 else x)

        # Lọc các cột số liệu, loại bỏ các cột ID gây nhiễu
        num_cols = final_df.select_dtypes(include=['number']).columns.tolist()
        exclude_cols = ['ID Trang', 'ID bài viết', 'ID tài sản video', 'ID video chung', 'ID tài khoản', 'Tổng lượt click', 'Lượt click khác']
        num_cols = [c for c in num_cols if c not in exclude_cols]
        
        if num_cols:
            st.sidebar.subheader(f"Cài đặt {platform_name}")
            sort_m = st.sidebar.selectbox(f"Xếp hạng theo ({platform_name}):", num_cols, key=f"sort_{platform_name}")
            
            final_df = final_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 nội dung {platform_name} cao nhất")
            fig = px.bar(final_df.head(10), x=sort_m, y='Tên hiển thị', orientation='h', text_auto=True, color_discrete_sequence=[chart_color])
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Bảng dữ liệu chi tiết")
            st.dataframe(final_df)
        else:
            st.warning("Không tìm thấy cột số liệu để xếp hạng.")
    else:
        st.info(f"Chưa tìm thấy file dữ liệu nào cho {platform_name}.")

# --- GIAO DIỆN 3 TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

with tab1:
    if page_dfs:
        merged = page_dfs[0]
        for next_df in page_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        merged['Ngày'] = pd.to_datetime(merged['Ngày']).dt.date
        metrics = [c for c in merged.columns if c != 'Ngày']
        
        st.sidebar.subheader("Cài đặt Tổng quan")
        sort_p = st.sidebar.selectbox("Sắp xếp Trang theo:", ["Ngày"] + metrics, key="sort_page")
        merged = merged.sort_values(sort_p, ascending=False)

        st.subheader("Biểu đồ xu hướng")
        selected = st.multiselect("Chọn chỉ số để xem:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
        if selected:
            fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected, markers=True, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged)
    else:
        st.warning("Chưa tìm thấy file dữ liệu Tổng quan Trang.")

with tab2:
    render_post_tab(fb_post_dfs, "Facebook", "#1877F2")

with tab3:
    render_post_tab(ig_post_dfs, "Insta", "#E1306C")
