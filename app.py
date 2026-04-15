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
            content = file_content.read()
            
        try:
            text = content.decode('utf-16')
        except UnicodeError:
            text = content.decode('utf-8')
        
        lines = text.splitlines()
        if len(lines) > 0 and 'sep=,' in lines[0]:
            lines = lines[2:]
            
        text = '\n'.join(lines)
        df = pd.read_csv(io.StringIO(text))
        
        # Làm sạch tên cột ngay từ đầu (xóa khoảng trắng thừa)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
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

# --- BẢNG ĐIỀU KHIỂN BÊN TRÁI ---
with st.sidebar:
    st.header("⚙️ Bảng Điều Khiển")
    
    sys_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    st.write("📁 **File trên Cloud (GitHub):**")
    if sys_files:
        for f in sys_files: 
            st.caption(f"☁️ {f}")
    else:
        st.caption("❌ Trống (Vui lòng upload lên GitHub)")
        
    st.markdown("---")
    st.info("💡 Tải thêm file CSV (Sẽ tự động gộp chung với dữ liệu Cloud):")
    extra_files = st.file_uploader("Kéo thả CSV tại đây", accept_multiple_files=True, type=['csv'])

# --- PHÂN LOẠI VÀ CHUẨN HÓA DỮ LIỆU ---
page_dfs, fb_post_dfs, ig_post_dfs = [], [], []

def classify_data(df_temp, f_name):
    if df_temp is not None and not df_temp.empty:
        f_lower = f_name.lower()
        
        # 1. ĐỒNG NHẤT CỘT NGÀY THÁNG TRƯỚC KHI LÀM BẤT CỨ VIỆC GÌ KHÁC
        date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
        if date_col:
            df_temp = df_temp.rename(columns={date_col: 'Ngày'})
            # Ép tất cả các thể loại định dạng ngày về chuẩn chung
            df_temp['Ngày'] = pd.to_datetime(df_temp['Ngày'], errors='coerce').dt.date
            df_temp = df_temp.dropna(subset=['Ngày']) 
        
        # 2. Phân loại Tab 1 (Tổng quan)
        if "Primary" in df_temp.columns or ("Lượt tương tác của người dùng" in df_temp.columns and "ID bài viết" not in df_temp.columns):
            if "Primary" in df_temp.columns:
                metric = f_name.replace(".csv", "").strip()
                df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
            else:
                # File mới: Chỉ giữ lại cột Ngày và các cột CHỨA SỐ (Loại bỏ ID Trang, Tên Trang)
                numeric_cols = df_temp.select_dtypes(include=['number']).columns.tolist()
                numeric_cols = [c for c in numeric_cols if 'ID' not in c] # Bỏ cột ID
                if 'Ngày' in df_temp.columns:
                    df_temp = df_temp[['Ngày'] + numeric_cols]
            
            # Xử lý số bị dính dấu phẩy (vd: 1,000 -> 1000)
            for col in df_temp.columns:
                if col != 'Ngày':
                    df_temp[col] = pd.to_numeric(df_temp[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    
            page_dfs.append(df_temp)
            
        # 3. Phân loại Tab 2 & 3 (Bài viết)
        else:
            if 'insta' in f_lower or 'ig' in f_lower:
                ig_post_dfs.append(df_temp)
            else:
                fb_post_dfs.append(df_temp)

# Quét file từ GitHub
for f_name in sys_files:
    classify_data(load_csv_smart(f_name, is_path=True), f_name)

# Quét file tải thêm
if extra_files:
    for file in extra_files:
        classify_data(load_csv_smart(file, is_path=False), file.name)

# --- HÀM VẼ GIAO DIỆN BÀI VIẾT ---
def render_post_tab(dfs_list, platform_name, chart_color):
    if dfs_list:
        final_df = pd.concat(dfs_list, ignore_index=True)
        final_df['Tên hiển thị'] = final_df.apply(get_post_name, axis=1)
        final_df['Tên hiển thị'] = final_df['Tên hiển thị'].apply(lambda x: x[:70] + "..." if len(x) > 70 else x)

        # Xử lý số liệu
        exclude_cols = ['ID Trang', 'ID bài viết', 'ID tài sản video', 'ID video chung', 'ID tài khoản']
        for col in final_df.columns:
            if col not in exclude_cols and col not in ['Tên hiển thị', 'Thời gian đăng', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả']:
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
        st.info(f"Chưa có dữ liệu. Vui lòng đảm bảo file CSV chứa chữ '{platform_name}' trong tên.")

# --- GIAO DIỆN 3 TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

with tab1:
    if page_dfs:
        merged = page_dfs[0]
        for next_df in page_dfs[1:]:
            merged = pd.merge(merged, next_df, on="Ngày", how="outer")
        
        # Nhóm dữ liệu theo ngày để phòng trường hợp có nhiều file đè lên nhau cùng 1 ngày
        merged = merged.groupby('Ngày').sum(numeric_only=True).reset_index()
        
        metrics = [c for c in merged.columns if c != 'Ngày']
        
        if metrics:
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
            st.warning("Không có cột số liệu hợp lệ nào để vẽ biểu đồ.")
    else:
        st.warning("Chưa có dữ liệu Tổng quan Trang.")

with tab2:
    render_post_tab(fb_post_dfs, "Facebook", "#1877F2")

with tab3:
    render_post_tab(ig_post_dfs, "Insta", "#E1306C")
