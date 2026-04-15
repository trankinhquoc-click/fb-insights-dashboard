import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Facebook Insights Dashboard - Sorting", page_icon="📈", layout="wide")
st.title("📈 Facebook Insights Dashboard (Sắp xếp theo hiệu quả)")

# --- HÀM HỖ TRỢ ĐỌC FILE ---
@st.cache_data
def load_csv_safe(file, skiprows=0):
    try:
        return pd.read_csv(file, skiprows=skiprows, encoding='utf-16')
    except:
        file.seek(0)
        return pd.read_csv(file, skiprows=skiprows, encoding='utf-8')

# --- CHIA TABS ---
tab1, tab2 = st.tabs(["📊 Tổng quan Trang", "📝 Hiệu quả Bài viết"])

# ==========================================
# TAB 1: TỔNG QUAN TRANG
# ==========================================
with tab1:
    st.header("📈 Phân tích Chỉ số Trang")
    page_files = st.file_uploader("Tải lên file dữ liệu Trang", accept_multiple_files=True, type=['csv'], key="page_up")
    
    if page_files:
        all_dfs = []
        for file in page_files:
            df = load_csv_safe(file, skiprows=2)
            if "Primary" in df.columns and "Ngày" in df.columns:
                metric_name = file.name.replace(".csv", "").strip()
                df = df.rename(columns={"Primary": metric_name})
                all_dfs.append(df)
        
        if all_dfs:
            merged = all_dfs[0]
            for next_df in all_dfs[1:]:
                merged = pd.merge(merged, next_df, on="Ngày", how="outer")
            
            merged['Ngày'] = pd.to_datetime(merged['Ngày']).dt.date
            
            # --- TÍNH NĂNG SẮP XẾP CHO TAB 1 ---
            metrics_list = merged.columns[1:].tolist()
            sort_page_by = st.selectbox("Sắp xếp bảng dữ liệu theo:", ["Ngày"] + metrics_list, index=0)
            
            # Thực hiện sắp xếp (Giảm dần nếu là số liệu)
            if sort_page_by == "Ngày":
                merged = merged.sort_values('Ngày', ascending=False)
            else:
                merged = merged.sort_values(sort_page_by, ascending=False)
            
            st.subheader("Biểu đồ xu hướng")
            selected_metrics = st.multiselect("Chọn chỉ số xem biểu đồ:", metrics_list, default=metrics_list[:2])
            if selected_metrics:
                fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected_metrics, markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Bảng dữ liệu (Đã sắp xếp)")
            st.dataframe(merged)

# ==========================================
# TAB 2: HIỆU QUẢ BÀI VIẾT
# ==========================================
with tab2:
    st.header("🏆 Xếp hạng Bài viết & Video")
    post_files = st.file_uploader("Tải lên file Bài viết/Video", accept_multiple_files=True, type=['csv'], key="post_up")
    
    if post_files:
        post_dfs = []
        for file in post_files:
            df = load_csv_safe(file, skiprows=0)
            if not df.empty:
                post_dfs.append(df)
        
        if post_dfs:
            final_df = pd.concat(post_dfs, ignore_index=True)
            
            # Xử lý tên bài viết
            name_col = 'Tiêu đề' if 'Tiêu đề' in final_df.columns else ('Mô tả' if 'Mô tả' in final_df.columns else None)
            if name_col:
                final_df['Tên hiển thị'] = final_df[name_col].fillna("Không có tiêu đề").astype(str).apply(lambda x: x[:50] + "...")
            else:
                final_df['Tên hiển thị'] = "Bài viết " + final_df.index.astype(str)

            # Lấy danh sách cột số liệu để sắp xếp
            numeric_cols = final_df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                # --- TÍNH NĂNG SẮP XẾP CHO TAB 2 ---
                sort_post_by = st.selectbox("Sắp xếp danh sách bài viết theo:", numeric_cols)
                
                # Sắp xếp toàn bộ dữ liệu theo số liệu từ cao xuống thấp
                final_df = final_df.sort_values(by=sort_post_by, ascending=False)
                
                # Vẽ biểu đồ Top 10
                st.subheader(f"Top 10 bài viết có {sort_post_by} cao nhất")
                top_10 = final_df.head(10)
                fig_post = px.bar(top_10, x=sort_post_by, y='Tên hiển thị', orientation='h', text_auto=True)
                fig_post.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_post, use_container_width=True)
                
                st.subheader("Danh sách chi tiết (Tất cả bài viết)")
                st.dataframe(final_df)
