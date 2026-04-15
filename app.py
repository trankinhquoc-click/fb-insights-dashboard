import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Facebook Insights Dashboard 2.0", page_icon="📈", layout="wide")
st.title("📈 Facebook Insights Dashboard 2.0")

# --- HÀM HỖ TRỢ ĐỌC FILE CHỐNG LỖI MÃ HÓA ---
@st.cache_data
def load_csv_safe(file, skiprows=0):
    try:
        # Ưu tiên đọc theo chuẩn UTF-16 của Facebook
        return pd.read_csv(file, skiprows=skiprows, encoding='utf-16')
    except UnicodeError:
        # Nếu lỗi, tự động lùi lại và đọc theo chuẩn UTF-8
        file.seek(0)
        return pd.read_csv(file, skiprows=skiprows, encoding='utf-8')
    except Exception:
        return pd.DataFrame() # Trả về bảng rỗng nếu có lỗi khác

# --- CHIA GIAO DIỆN THÀNH 2 TABS ---
tab1, tab2 = st.tabs(["📊 Tổng quan Trang (Page Level)", "📝 Hiệu quả Bài viết (Post Level)"])

# ==========================================
# TAB 1: TỔNG QUAN TRANG (Dành cho 6 file cũ)
# ==========================================
with tab1:
    st.header("📈 Phân tích Tổng quan Trang")
    st.info("Kéo thả 6 file chỉ số hàng ngày (VD: Lượt xem.csv, Lượt truy cập.csv...) vào khu vực bên dưới.")
    
    page_files = st.file_uploader("Tải lên file dữ liệu Trang", accept_multiple_files=True, type=['csv'], key="page_uploader")
    
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
            merged = merged.sort_values('Ngày')
            
            st.success("Tải dữ liệu Trang thành công!")
            
            # Vẽ biểu đồ xu hướng
            st.subheader("Biểu đồ xu hướng theo ngày")
            selected_metrics = st.multiselect("Chọn chỉ số để so sánh:", merged.columns[1:], default=merged.columns[1:3])
            if selected_metrics:
                fig = px.line(merged, x='Ngày', y=selected_metrics, markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(merged)
        else:
            st.warning("Vui lòng tải đúng các file chỉ số của Trang.")

# ==========================================
# TAB 2: HIỆU QUẢ BÀI VIẾT (Dành cho các file mới)
# ==========================================
with tab2:
    st.header("🏆 Bảng xếp hạng Hiệu quả Bài viết & Video")
    st.info("Kéo thả các file có tên dài (VD: Mar-16-2026_Apr...) vào đây. Lưu ý: Không dùng file 'Định dạng nội dung hàng đầu' ở đây.")
    
    post_files = st.file_uploader("Tải lên file dữ liệu Bài viết/Video", accept_multiple_files=True, type=['csv'], key="post_uploader")
    
    if post_files:
        post_dfs = []
        for file in post_files:
            df = load_csv_safe(file, skiprows=0) # File bài viết không có dòng thừa
            if not df.empty:
                post_dfs.append(df)
        
        if post_dfs:
            # Gộp danh sách các bài viết lại
            final_post_df = pd.concat(post_dfs, ignore_index=True)
            
            # Tạo tên bài viết hiển thị (Ưu tiên Tiêu đề, nếu trống dùng Mô tả)
            if 'Tiêu đề' in final_post_df.columns and 'Mô tả' in final_post_df.columns:
                final_post_df['Tên bài viết'] = final_post_df['Tiêu đề'].fillna(final_post_df['Mô tả'])
            elif 'Mô tả' in final_post_df.columns:
                final_post_df['Tên bài viết'] = final_post_df['Mô tả']
            else:
                final_post_df['Tên bài viết'] = "Bài viết không có tiêu đề"
            
            # Cắt ngắn tên bài viết nếu quá dài để biểu đồ không bị vỡ
            final_post_df['Tên bài viết'] = final_post_df['Tên bài viết'].astype(str).apply(lambda x: x[:50] + "..." if len(x) > 50 else x)
            
            # Tự động dò tìm các cột số liệu quan trọng đang có
            available_metrics = []
            for m in ["Lượt xem", "Số người tiếp cận", "Lượt tương tác", "Cảm xúc", "Bình luận", "Lượt chia sẻ"]:
                if m in final_post_df.columns:
                    available_metrics.append(m)
            
            if available_metrics:
                st.success(f"Đã phân tích thành công {len(final_post_df)} bài viết/video!")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.subheader("Tùy chọn xếp hạng")
                    sort_by = st.selectbox("Sắp xếp bài viết theo:", available_metrics)
                    
                    # Chuyển đổi dữ liệu sang số và lọc Top 10
                    final_post_df[sort_by] = pd.to_numeric(final_post_df[sort_by], errors='coerce').fillna(0)
                    top_posts = final_post_df.sort_values(by=sort_by, ascending=False).head(10)
                    
                with col2:
                    st.subheader(f"Top 10 Bài viết có {sort_by} cao nhất")
                    fig_post = px.bar(top_posts, x=sort_by, y='Tên bài viết', orientation='h', text_auto=True)
                    fig_post.update_layout(yaxis={'categoryorder':'total ascending'}) # Bài cao nhất nằm trên cùng
                    st.plotly_chart(fig_post, use_container_width=True)
                    
                st.subheader("Dữ liệu chi tiết từng bài viết")
                display_cols = ['Thời gian đăng', 'Tên bài viết'] + available_metrics
                st.dataframe(final_post_df[display_cols])
            else:
                st.warning("Không tìm thấy cột số liệu tương tác nào trong file này.")
