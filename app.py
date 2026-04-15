import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Facebook Insights 2.6", page_icon="🚀", layout="wide")
st.title("🚀 Facebook Insights - Bản Quét Dữ Liệu Tự Động")

# --- HÀM ĐỌC FILE CHỐNG LỖI MÃ HÓA ---
def load_csv_smart(file_path):
    try:
        # Thử đọc chuẩn UTF-16 của Facebook
        df = pd.read_csv(file_path, skiprows=2, encoding='utf-16')
        if 'Ngày' not in df.columns: # Nếu không phải file Trang 2 dòng rác
            df = pd.read_csv(file_path, encoding='utf-16')
    except:
        try:
            # Thử đọc chuẩn UTF-8
            df = pd.read_csv(file_path, skiprows=2, encoding='utf-8')
            if 'Ngày' not in df.columns:
                df = pd.read_csv(file_path, encoding='utf-8')
        except:
            return None
    return df

# --- TỰ ĐỘNG QUÉT VÀ PHÂN LOẠI FILE ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
page_dfs = []
post_dfs = []

for f_name in all_files:
    df_temp = load_csv_smart(f_name)
    if df_temp is not None:
        # Phân loại vào Tab 1: Nếu có cột Primary hoặc chỉ số Trang đặc thù
        if "Primary" in df_temp.columns or "Lượt tương tác của người dùng" in df_temp.columns:
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            page_dfs.append(df_temp)
        
        # Phân loại vào Tab 2: Nếu có cột ID bài viết hoặc ID video
        elif "ID bài viết" in df_temp.columns or "ID tài sản video" in df_temp.columns:
            post_dfs.append(df_temp)

# --- GIAO DIỆN TABS ---
tab1, tab2 = st.tabs(["📊 Tổng quan Trang", "📝 Hiệu quả Bài viết"])

# ==========================================
# TAB 1: TỔNG QUAN TRANG
# ==========================================
with tab1:
    if page_dfs:
        merged = page_dfs[0]
        for next_df in page_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        merged['Ngày'] = pd.to_datetime(merged['Ngày']).dt.date
        metrics = merged.columns[1:].tolist()
        
        # Sắp xếp theo số liệu cao nhất (Yêu cầu của bạn)
        st.sidebar.subheader("Cài đặt Tab 1")
        sort_p = st.sidebar.selectbox("Sắp xếp Trang theo:", ["Ngày"] + metrics)
        merged = merged.sort_values(sort_p, ascending=False)

        st.subheader("Biểu đồ xu hướng")
        selected = st.multiselect("Chọn chỉ số:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
        if selected:
            fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected, markers=True)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged)
    else:
        st.warning("Chưa tìm thấy file dữ liệu Trang (.csv) nào trong thư mục.")

# ==========================================
# TAB 2: HIỆU QUẢ BÀI VIẾT
# ==========================================
with tab2:
    if post_dfs:
        final_post_df = pd.concat(post_dfs, ignore_index=True)
        
        # Tìm cột tên hiển thị
        name_col = next((c for c in ["Tiêu đề", "Mô tả", "Nội dung"] if c in final_post_df.columns), None)
        final_post_df['Tên hiển thị'] = final_post_df[name_col].fillna("Bài không tiêu đề").astype(str).apply(lambda x: x[:50] + "...") if name_col else "Nội dung"

        # Lấy các cột số liệu
        num_cols = final_post_df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            st.sidebar.subheader("Cài đặt Tab 2")
            sort_m = st.sidebar.selectbox("Xếp hạng bài viết theo:", num_cols)
            
            # Sắp xếp từ cao xuống thấp
            final_post_df = final_post_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"Top 10 nội dung có {sort_m} cao nhất")
            fig_post = px.bar(final_post_df.head(10), x=sort_m, y='Tên hiển thị', orientation='h', text_auto=True)
            fig_post.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_post, use_container_width=True)
            
            st.dataframe(final_post_df)
    else:
        st.warning("Chưa tìm thấy file dữ liệu Bài viết (.csv) nào trong thư mục.")
