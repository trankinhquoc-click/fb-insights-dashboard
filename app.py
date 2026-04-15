import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Auto Dashboard", page_icon="📈", layout="wide")
st.title("📈 Facebook Insights - Báo cáo tự động")

# --- HÀM ĐỌC FILE TỪ THƯ MỤC ---
def load_local_csv(file_path, skiprows=0):
    try:
        # Thử đọc UTF-16
        return pd.read_csv(file_path, skiprows=skiprows, encoding='utf-16')
    except:
        # Nếu lỗi thì đọc UTF-8
        return pd.read_csv(file_path, skiprows=skiprows, encoding='utf-8')

# --- DANH SÁCH FILE CẦN ĐỌC ---
# Bạn có thể thêm bớt tên file chính xác ở đây
page_filenames = [
    "Lượt xem.csv", "Lượt theo dõi.csv", "Lượt truy cập.csv", 
    "Lượt click vào liên kết.csv", "Lượt tương tác.csv", "Người xem.csv",
    "Mar-17-2026_Apr-14-2026_725341394002400.csv"
]

post_filenames = [
    "Mar-16-2026_Apr-12-2026_2018054159067141.csv",
    "Mar-16-2026_Apr-12-2026_1637348910867738.csv",
    "Mar-16-2026_Apr-12-2026_1513457057006769.csv",
    "Mar-17-2026_Apr-14-2026_968814768944809.csv"
]

tab1, tab2 = st.tabs(["📊 Tổng quan Trang", "📝 Hiệu quả Bài viết"])

# ==========================================
# TAB 1: TỔNG QUAN TRANG
# ==========================================
with tab1:
    all_dfs = []
    for f_name in page_filenames:
        if os.path.exists(f_name):
            df = load_local_csv(f_name, skiprows=2)
            # Kiểm tra định dạng cũ (có cột Primary)
            if "Primary" in df.columns and "Ngày" in df.columns:
                metric = f_name.replace(".csv", "")
                df = df[['Ngày', 'Primary']].rename(columns={"Primary": metric})
                all_dfs.append(df)
            # Kiểm tra định dạng mới (file 7253...)
            elif "Ngày" in df.columns and "Lượt tương tác của người dùng" in df.columns:
                df = df[['Ngày', 'Lượt tương tác của người dùng']]
                all_dfs.append(df)

    if all_dfs:
        merged = all_dfs[0]
        for next_df in all_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        merged['Ngày'] = pd.to_datetime(merged['Ngày']).dt.date
        
        # Sắp xếp theo số liệu cao nhất (Yêu cầu của bạn)
        metrics_list = merged.columns[1:].tolist()
        sort_by = st.selectbox("Sắp xếp bảng theo:", metrics_list, index=0)
        merged = merged.sort_values(sort_by, ascending=False)

        st.subheader("Biểu đồ xu hướng")
        fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=metrics_list, markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Bảng dữ liệu chi tiết")
        st.dataframe(merged)
    else:
        st.error("Không tìm thấy các file dữ liệu Trang trên hệ thống.")

# ==========================================
# TAB 2: HIỆU QUẢ BÀI VIẾT
# ==========================================
with tab2:
    post_dfs = []
    for f_name in post_filenames:
        if os.path.exists(f_name):
            df = load_local_csv(f_name, skiprows=0)
            post_dfs.append(df)

    if post_dfs:
        final_df = pd.concat(post_dfs, ignore_index=True)
        
        # Xử lý tên hiển thị
        name_col = 'Tiêu đề' if 'Tiêu đề' in final_df.columns else ('Mô tả' if 'Mô tả' in final_df.columns else None)
        final_df['Tên hiển thị'] = final_df[name_col].fillna("Không tiêu đề").astype(str).apply(lambda x: x[:50] + "...") if name_col else "Video/Post"

        numeric_cols = final_df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            sort_metric = st.selectbox("Xếp hạng bài viết theo:", numeric_cols)
            final_df = final_df.sort_values(by=sort_metric, ascending=False)
            
            st.subheader(f"Top 10 nội dung có {sort_metric} cao nhất")
            fig_post = px.bar(final_df.head(10), x=sort_metric, y='Tên hiển thị', orientation='h', text_auto=True)
            fig_post.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_post, use_container_width=True)
            
            st.subheader("Danh sách chi tiết")
            st.dataframe(final_df)
    else:
        st.error("Không tìm thấy các file dữ liệu Bài viết trên hệ thống.")
