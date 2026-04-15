import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - FB & IG Dashboard", page_icon="🚀", layout="wide")
st.title("🚀 Dashboard Facebook & Instagram (Bản 2.9 - Hoàn Hảo)")

# --- HÀM ĐỌC FILE CHỐNG VỠ DỮ LIỆU ---
@st.cache_data
def load_csv_smart(file_path):
    for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
        try:
            # Đọc toàn bộ để không làm vỡ các bài viết có dấu xuống dòng
            df = pd.read_csv(file_path, encoding=enc)
            # Xử lý dòng rác sep=, nếu có
            if not df.empty and len(df.columns) == 1 and 'sep=' in str(df.columns[0]).lower():
                df = pd.read_csv(file_path, encoding=enc, skiprows=2)
                if len(df.columns) < 2: 
                    df = pd.read_csv(file_path, encoding=enc, skiprows=1)
            
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns] # Xóa khoảng trắng tên cột
                return df
        except:
            continue
    return None

# --- HÀM XỬ LÝ TÊN THÔNG MINH ---
def get_channel_name(row, f_name):
    for col in ["Tên Trang", "Tên người dùng tài khoản", "Tên tài khoản"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
    # Nếu file là Facebook.csv hoặc Insta.csv thì lấy luôn tên đó
    f_clean = f_name.replace(".csv", "").capitalize()
    return f_clean

def get_post_content(row):
    for col in ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
    return "Nội dung không có tiêu đề"

# --- QUÉT VÀ PHÂN LOẠI FILE ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
page_dfs = []
post_dfs = []

for f_name in all_files:
    df_temp = load_csv_smart(f_name)
    if df_temp is not None and not df_temp.empty:
        # Tìm cột ngày
        date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
        if not date_col: continue

        # Kiểm tra xem có phải file Bài viết không
        is_post = any(c in df_temp.columns for c in ["Thời gian đăng", "Liên kết vĩnh viễn", "ID bài viết", "ID tài sản video"])
        
        if is_post:
            df_temp['Kênh'] = df_temp.apply(lambda r: get_channel_name(r, f_name), axis=1)
            df_temp['Nội dung hiển thị'] = df_temp.apply(get_post_content, axis=1)
            post_dfs.append(df_temp)
        else:
            # Xử lý file Tổng quan (Tab 1)
            df_temp = df_temp.rename(columns={date_col: 'Ngày'})
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            else:
                # Giữ lại Ngày và các cột số, bỏ ID
                cols_to_keep = ['Ngày'] + [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                df_temp = df_temp[cols_to_keep]
            page_dfs.append(df_temp)

# --- GIAO DIỆN TABS ---
tab1, tab2 = st.tabs(["📊 Tổng quan Trang", "📝 Hiệu quả Bài viết"])

# ==========================================
# TAB 1: TỔNG QUAN TRANG (ĐÃ KHÔI PHỤC)
# ==========================================
with tab1:
    if page_dfs:
        merged = page_dfs[0]
        for next_df in page_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        merged['Ngày'] = pd.to_datetime(merged['Ngày'], errors='coerce').dt.date
        merged = merged.dropna(subset=['Ngày'])
        metrics = [c for c in merged.columns if c != 'Ngày']
        
        if metrics:
            st.sidebar.subheader("Cài đặt Trang")
            sort_p = st.sidebar.selectbox("Sắp xếp bảng theo:", ["Ngày"] + metrics)
            merged = merged.sort_values(sort_p, ascending=False)

            st.subheader("Biểu đồ xu hướng")
            selected = st.multiselect("Chọn chỉ số:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
            if selected:
                fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected, markers=True)
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(merged)
    else:
        st.warning("Chưa tìm thấy dữ liệu Tổng quan Trang.")

# ==========================================
# TAB 2: HIỆU QUẢ BÀI VIẾT (GỘP KÊNH THÔNG MINH)
# ==========================================
with tab2:
    if post_dfs:
        final_post_df = pd.concat(post_dfs, ignore_index=True)
        final_post_df['Nội dung hiển thị'] = final_post_df['Nội dung hiển thị'].apply(lambda x: str(x)[:60] + "..." if len(str(x)) > 60 else str(x))

        # Xử lý số liệu
        exclude = ['ID', 'Kênh', 'Nội dung hiển thị', 'Thời gian đăng', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']
        for col in final_post_df.columns:
            if col not in exclude and final_post_df[col].dtype == 'object':
                try:
                    final_post_df[col] = pd.to_numeric(final_post_df[col].astype(str).str.replace(',', ''), errors='ignore')
                except: pass
                    
        num_cols = [c for c in final_post_df.columns if final_post_df[c].dtype in ['float64', 'int64'] and not any(ex in c for ex in exclude)]
        
        if num_cols:
            st.sidebar.subheader("Cài đặt Bài viết")
            sort_m = st.sidebar.selectbox("Xếp hạng bài viết theo:", num_cols)
            final_post_df = final_post_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 nội dung có {sort_m} cao nhất")
            fig_post = px.bar(final_post_df.head(10), x=sort_m, y='Nội dung hiển thị', color='Kênh', orientation='h', text_auto=True)
            fig_post.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_post, use_container_width=True)
            
            # Sắp xếp lại cột cho bảng dữ liệu đẹp mắt
            cols_to_show = ['Kênh', 'Thời gian đăng', 'Nội dung hiển thị'] + num_cols
            st.dataframe(final_post_df[[c for c in cols_to_show if c in final_post_df.columns]])
    else:
        st.error("Chưa tìm thấy dữ liệu Bài viết.")
