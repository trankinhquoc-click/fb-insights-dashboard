import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Đa Nền Tảng", page_icon="🚀", layout="wide")
st.title("🚀 Dashboard Phân Tích: Facebook & Instagram")

# --- HÀM ĐỌC FILE CHỐNG LỖI MÃ HÓA ---
def load_csv_smart(file_path):
    try:
        df = pd.read_csv(file_path, skiprows=2, encoding='utf-16')
        if 'Ngày' not in df.columns and len(df.columns) < 3: 
            df = pd.read_csv(file_path, encoding='utf-16')
    except:
        try:
            df = pd.read_csv(file_path, skiprows=2, encoding='utf-8')
            if 'Ngày' not in df.columns and len(df.columns) < 3:
                df = pd.read_csv(file_path, encoding='utf-8')
        except:
            return None
    return df

# --- QUÉT VÀ PHÂN LOẠI FILE TỰ ĐỘNG ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
page_dfs = []
fb_post_dfs = []
ig_post_dfs = []

for f_name in all_files:
    df_temp = load_csv_smart(f_name)
    if df_temp is not None:
        f_lower = f_name.lower()
        
        # 1. Nhận diện file Tổng quan Trang (Page Level)
        if "Primary" in df_temp.columns or ("Lượt tương tác của người dùng" in df_temp.columns and "ID bài viết" not in df_temp.columns):
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            page_dfs.append(df_temp)
            
        # 2. Nhận diện file Bài viết / Video (Post Level)
        else:
            if 'insta' in f_lower or 'ig' in f_lower:
                ig_post_dfs.append(df_temp)
            elif 'facebook' in f_lower or 'fb' in f_lower:
                fb_post_dfs.append(df_temp)
            else:
                # Nếu file không có chữ FB/IG, đưa tạm vào danh sách Facebook
                fb_post_dfs.append(df_temp)

# --- HÀM VẼ GIAO DIỆN CHUNG CHO TAB BÀI VIẾT ---
def render_post_tab(dfs_list, platform_name, chart_color):
    if dfs_list:
        final_df = pd.concat(dfs_list, ignore_index=True)
        
        # Tìm cột tên hiển thị (Instagram đôi khi không có Tiêu đề, nên dùng Liên kết vĩnh viễn)
        name_cols = ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]
        name_col = next((c for c in name_cols if c in final_df.columns), None)
        
        if name_col:
            final_df['Tên hiển thị'] = final_df[name_col].fillna(f"Nội dung {platform_name}").astype(str).apply(lambda x: x[:60] + "..." if len(x) > 60 else x)
        else:
            final_df['Tên hiển thị'] = f"Nội dung {platform_name} không tên"

        # Lấy các cột số liệu, loại bỏ các cột ID không cần thiết
        num_cols = final_df.select_dtypes(include=['number']).columns.tolist()
        exclude_cols = ['ID Trang', 'ID bài viết', 'ID tài sản video', 'ID video chung', 'ID tài khoản']
        num_cols = [c for c in num_cols if c not in exclude_cols]
        
        if num_cols:
            st.sidebar.subheader(f"Cài đặt {platform_name}")
            sort_m = st.sidebar.selectbox(f"Xếp hạng {platform_name} theo:", num_cols, key=f"sort_{platform_name}")
            
            final_df = final_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 nội dung {platform_name} cao nhất")
            fig = px.bar(final_df.head(10), x=sort_m, y='Tên hiển thị', orientation='h', text_auto=True, color_discrete_sequence=[chart_color])
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Bảng dữ liệu chi tiết")
            st.dataframe(final_df)
        else:
            st.warning("Không tìm thấy cột số liệu nào phù hợp để xếp hạng.")
            st.dataframe(final_df)
    else:
        st.info(f"Chưa tìm thấy file dữ liệu nào cho {platform_name} (Hãy đảm bảo tên file có chữ '{platform_name}').")

# --- GIAO DIỆN 3 TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

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
        
        st.sidebar.subheader("Cài đặt Tổng quan")
        sort_p = st.sidebar.selectbox("Sắp xếp Trang theo:", ["Ngày"] + metrics, key="sort_page")
        merged = merged.sort_values(sort_p, ascending=False)

        st.subheader("Biểu đồ xu hướng")
        selected = st.multiselect("Chọn chỉ số:", metrics, default=metrics[:2] if len(metrics)>1 else metrics)
        if selected:
            fig = px.line(merged.sort_values('Ngày'), x='Ngày', y=selected, markers=True, color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(merged)
    else:
        st.warning("Chưa tìm thấy file dữ liệu Tổng quan Trang.")

# ==========================================
# TAB 2 & 3: HIỆU QUẢ NỘI DUNG FB & IG
# ==========================================
with tab2:
    render_post_tab(fb_post_dfs, "Facebook", "#1877F2")

with tab3:
    render_post_tab(ig_post_dfs, "Insta", "#E1306C")
