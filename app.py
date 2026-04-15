import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Dashboard v2.9.1", page_icon="🚀", layout="wide")
st.title("🚀 Dashboard Facebook & Instagram (Bản 2.9.1 - Cloud Optimized)")

# --- HÀM ĐỌC FILE SIÊU CỨNG CÁP ---
@st.cache_data
def load_csv_smart(file_path):
    for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            # Xử lý mã hóa
            try:
                text = content.decode(enc)
            except:
                continue
                
            # Xử lý dòng rác sep=,
            lines = text.splitlines()
            if len(lines) > 0 and 'sep=' in lines[0].lower():
                lines = lines[2:]
            text = '\n'.join(lines)
            
            df = pd.read_csv(io.StringIO(text))
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except:
            continue
    return None

# --- CHẨN ĐOÁN FILE TRÊN CLOUD ---
with st.sidebar:
    st.header("📂 Hệ thống file trên Cloud")
    all_csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if all_csv_files:
        st.success(f"Tìm thấy {len(all_csv_files)} file CSV")
        for f in all_csv_files:
            st.caption(f"✅ {f}")
    else:
        st.error("❌ Không tìm thấy file .csv nào trên GitHub!")
    st.markdown("---")

# --- PHÂN LOẠI DỮ LIỆU ---
page_dfs = []
post_dfs = []

for f_name in all_csv_files:
    df_temp = load_csv_smart(f_name)
    if df_temp is not None and not df_temp.empty:
        # Tìm cột ngày linh hoạt hơn
        date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
        
        # Nhận diện file Bài viết
        is_post = any(c in df_temp.columns for c in ["Thời gian đăng", "Liên kết vĩnh viễn", "ID bài viết", "ID tài sản video"])
        
        if is_post:
            # Xử lý tên kênh và nội dung
            name_cols = ["Tên Trang", "Tên người dùng tài khoản", "Tên tài khoản"]
            channel = next((str(df_temp[c].iloc[0]) for c in name_cols if c in df_temp.columns and pd.notna(df_temp[c].iloc[0])), f_name.replace(".csv", ""))
            df_temp['Kênh'] = channel
            
            content_cols = ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]
            def get_content(row):
                for c in content_cols:
                    if c in row and pd.notna(row[c]): return str(row[c])
                return "Nội dung trống"
            df_temp['Nội dung hiển thị'] = df_temp.apply(get_content, axis=1)
            post_dfs.append(df_temp)
        
        elif date_col:
            # Xử lý file Tổng quan
            df_temp = df_temp.rename(columns={date_col: 'Ngày'})
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            else:
                numeric_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                df_temp = df_temp[['Ngày'] + numeric_cols]
            page_dfs.append(df_temp)

# --- GIAO DIỆN TABS ---
tab1, tab2 = st.tabs(["📊 Tổng quan Trang", "📝 Hiệu quả Bài viết"])

with tab1:
    if page_dfs:
        merged = page_dfs[0]
        for next_df in page_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        merged['Ngày'] = pd.to_datetime(merged['Ngày'], errors='coerce').dt.date
        merged = merged.dropna(subset=['Ngày']).sort_values('Ngày', ascending=False)
        metrics = [c for c in merged.columns if c != 'Ngày']
        
        if metrics:
            st.subheader("Biểu đồ xu hướng")
            selected = st.multiselect("Chọn chỉ số:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
            if selected:
                fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected, markers=True)
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(merged)
    else:
        st.warning("Chưa tìm thấy dữ liệu Tổng quan Trang. Hãy kiểm tra danh sách file ở thanh bên trái.")

with tab2:
    if post_dfs:
        final_post_df = pd.concat(post_dfs, ignore_index=True)
        final_post_df['Nội dung hiển thị'] = final_post_df['Nội dung hiển thị'].apply(lambda x: str(x)[:60] + "..." if len(str(x)) > 60 else str(x))
        
        # Xử lý số liệu
        exclude = ['ID', 'Kênh', 'Nội dung hiển thị', 'Thời gian đăng', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả']
        num_cols = [c for c in final_post_df.columns if final_post_df[c].dtype in ['float64', 'int64'] and not any(ex in c for ex in exclude)]
        
        if num_cols:
            sort_m = st.sidebar.selectbox("Xếp hạng theo:", num_cols, key="sort_post")
            final_post_df = final_post_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 nội dung có {sort_m} cao nhất")
            fig_post = px.bar(final_post_df.head(10), x=sort_m, y='Nội dung hiển thị', color='Kênh', orientation='h', text_auto=True)
            fig_post.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_post, use_container_width=True)
            st.dataframe(final_post_df[['Kênh', 'Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
    else:
        st.error("Chưa tìm thấy dữ liệu Bài viết.")
