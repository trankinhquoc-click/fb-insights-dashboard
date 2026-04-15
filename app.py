import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Dashboard v3.8", page_icon="📈", layout="wide")
st.title("📈 Dashboard Phân Tích: Facebook & Instagram")

# --- HÀM ĐỌC FILE CHỐNG VỠ DỮ LIỆU ---
@st.cache_data
def load_csv_smart(file_path):
    for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            if not df.empty and len(df.columns) == 1 and 'sep=' in str(df.columns[0]).lower():
                df = pd.read_csv(file_path, encoding=enc, skiprows=2)
                if len(df.columns) < 2:
                    df = pd.read_csv(file_path, encoding=enc, skiprows=1)
            
            if not df.empty and len(df.columns) > 1:
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except Exception:
            continue
    return None

# --- HÀM TÌM TÊN BÀI VIẾT ---
def get_post_name(row):
    for col in ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
    return "Nội dung không có tiêu đề"

# --- CHUẨN HÓA SỐ LIỆU ---
def clean_numeric_df(df):
    exclude = ['ID', 'Ngày', 'Thời gian đăng', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Nội dung hiển thị']
    for col in df.columns:
        if not any(ex in col for ex in exclude) and df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
            except: pass
    return df

# --- DANH SÁCH 6 FILE TỔNG QUAN CHỈ ĐỊNH ---
target_page_files = [
    "Lượt click vào liên kết.csv", 
    "Lượt theo dõi.csv", 
    "Lượt truy cập.csv", 
    "Lượt tương tác.csv", 
    "Lượt xem.csv", 
    "Người xem.csv"
]
target_page_files_lower = [f.lower() for f in target_page_files]

# --- BẢN TIN CHẨN ĐOÁN (SIDEBAR) ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
fb_file = next((f for f in all_files if 'facebook' in f.lower()), None)
ig_file = next((f for f in all_files if 'insta' in f.lower() or 'ig' in f.lower()), None)

with st.sidebar:
    st.header("🔍 Trạng thái hệ thống")
    st.write("📘 **File Bài viết:**")
    if fb_file: st.caption(f"✅ Đã nhận: {fb_file}")
    else: st.caption("❌ Thiếu: Facebook.csv")
    if ig_file: st.caption(f"✅ Đã nhận: {ig_file}")
    else: st.caption("❌ Thiếu: Insta.csv")
    
    st.write("📊 **6 File Tổng quan:**")
    for target in target_page_files:
        if any(f.lower() == target.lower() for f in all_files):
            st.caption(f"✅ {target}")
        else:
            st.caption(f"❌ Thiếu: {target}")
    st.markdown("---")

# --- PHÂN LOẠI DỮ LIỆU ---
page_dfs = []
fb_df = load_csv_smart(fb_file) if fb_file else None
ig_df = load_csv_smart(ig_file) if ig_file else None

for f_name in all_files:
    f_lower = f_name.lower()
    
    # CHỈ ĐỌC NẾU TÊN FILE NẰM TRONG DANH SÁCH 6 FILE TỔNG QUAN
    if f_lower in target_page_files_lower:
        df_temp = load_csv_smart(f_name)
        if df_temp is not None and not df_temp.empty:
            date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
            if date_col:
                df_temp = df_temp.rename(columns={date_col: 'Ngày'})
                # Lấy tên cột là tên file (ví dụ: Lượt xem)
                metric_name = f_name.replace(".csv", "").replace(".CSV", "").strip()
                
                # Trích xuất dữ liệu
                if "Primary" in df_temp.columns:
                    df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric_name})
                    page_dfs.append(df_temp)
                else:
                    # Nếu mất cột Primary, lấy cột số đầu tiên
                    num_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                    if num_cols:
                        df_temp = df_temp[['Ngày', num_cols[0]]].rename(columns={num_cols[0]: metric_name})
                        page_dfs.append(df_temp)

# --- GIAO DIỆN CHÍNH ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

# ==========================================
# TAB 1: TỔNG QUAN (ĐÃ FIX LỖI KEYERROR)
# ==========================================
with tab1:
    # Lọc lại một lần nữa để chắc chắn 100% các bảng đều có cột 'Ngày'
    valid_dfs = [df for df in page_dfs if 'Ngày' in df.columns]
    
    if valid_dfs:
        merged = valid_dfs[0]
        for next_df in valid_dfs[1:]:
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
            st.warning("Không có cột dữ liệu số nào để hiển thị.")
    else:
        st.warning("Chưa có dữ liệu Tổng quan. Vui lòng kiểm tra thanh bên trái để xem các file bị thiếu.")

# ==========================================
# TAB 2: FACEBOOK (GIỮ Y NGUYÊN)
# ==========================================
with tab2:
    if fb_df is not None:
        fb_df = clean_numeric_df(fb_df)
        fb_df['Nội dung hiển thị'] = fb_df.apply(get_post_name, axis=1)
        
        num_cols = [c for c in fb_df.columns if fb_df[c].dtype in ['float64', 'int64'] and 'ID' not in c]
        if num_cols:
            sort_fb = st.sidebar.selectbox("Sắp xếp Facebook theo:", num_cols, key="sb_fb")
            fb_df = fb_df.sort_values(sort_fb, ascending=False)
            
            st.subheader(f"🏆 Top 10 Facebook ({sort_fb})")
            fig_fb = px.bar(fb_df.head(10), x=sort_fb, y=fb_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2'])
            fig_fb.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
            st.plotly_chart(fig_fb, use_container_width=True)
            st.dataframe(fb_df[['Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
        else:
            st.warning("Không tìm thấy các cột số liệu tương tác trong file Facebook.csv")
    else:
        st.error("Dữ liệu Facebook bị lỗi định dạng hoặc chưa tải lên.")

# ==========================================
# TAB 3: INSTAGRAM (GIỮ Y NGUYÊN)
# ==========================================
with tab3:
    if ig_df is not None:
        ig_df = clean_numeric_df(ig_df)
        ig_df['Nội dung hiển thị'] = ig_df.apply(get_post_name, axis=1)
        
        num_cols = [c for c in ig_df.columns if ig_df[c].dtype in ['float64', 'int64'] and 'ID' not in c]
        if num_cols:
            sort_ig = st.sidebar.selectbox("Sắp xếp Instagram theo:", num_cols, key="sb_ig")
            ig_df = ig_df.sort_values(sort_ig, ascending=False)
            
            st.subheader(f"🏆 Top 10 Instagram ({sort_ig})")
            fig_ig = px.bar(ig_df.head(10), x=sort_ig, y=ig_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C'])
            fig_ig.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
            st.plotly_chart(fig_ig, use_container_width=True)
            st.dataframe(ig_df[['Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
        else:
            st.warning("Không tìm thấy các cột số liệu tương tác trong file Insta.csv")
    else:
        st.error("Dữ liệu Instagram bị lỗi định dạng hoặc chưa tải lên.")
