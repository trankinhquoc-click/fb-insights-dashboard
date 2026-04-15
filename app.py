import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Dashboard v3.5", page_icon="🚀", layout="wide")
st.title("🚀 Dashboard Phân Tích: Facebook & Instagram")

# --- HÀM ĐỌC FILE SIÊU CỨNG CÁP ---
@st.cache_data
def load_csv_smart(file_path):
    for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            try:
                text = content.decode(enc)
            except:
                continue
            
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

# --- HÀM TÌM TÊN BÀI VIẾT THÔNG MINH ---
def get_post_name(row):
    for col in ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
    return "Nội dung không có tiêu đề"

# --- CHUẨN HÓA SỐ LIỆU ---
def clean_numeric_df(df):
    exclude = ['ID', 'Ngày', 'Thời gian đăng', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Nội dung hiển thị', 'Tên Trang', 'Tên người dùng tài khoản']
    for col in df.columns:
        if not any(ex in col for ex in exclude) and df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
            except: pass
    return df

# --- PHÂN LOẠI FILE ĐÍCH DANH ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
page_dfs = []
fb_df = None
ig_df = None

for f_name in all_files:
    f_lower = f_name.lower()
    
    if f_lower == "facebook.csv":
        fb_df = load_csv_smart(f_name)
    elif f_lower == "insta.csv":
        ig_df = load_csv_smart(f_name)
    else:
        # Gom các file còn lại vào Tổng quan (nếu có cột Ngày)
        df_temp = load_csv_smart(f_name)
        if df_temp is not None:
            date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
            if date_col:
                df_temp = df_temp.rename(columns={date_col: 'Ngày'})
                if "Primary" in df_temp.columns:
                    metric = f_name.replace(".csv", "").strip()
                    df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric})
                else:
                    num_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                    df_temp = df_temp[['Ngày'] + num_cols]
                page_dfs.append(df_temp)

# --- GIAO DIỆN 3 TABS RIÊNG BIỆT ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

# ==========================================
# TAB 1: TỔNG QUAN TRANG
# ==========================================
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
        st.warning("Chưa tìm thấy dữ liệu Tổng quan (Lượt xem, Tương tác...). Hãy đảm bảo các file này đã có trên GitHub.")

# ==========================================
# TAB 2: HIỆU QUẢ FACEBOOK (FILE Facebook.csv)
# ==========================================
with tab2:
    if fb_df is not None:
        fb_df = clean_numeric_df(fb_df)
        fb_df['Nội dung hiển thị'] = fb_df.apply(get_post_name, axis=1)
        
        # Lấy cột số liệu
        exclude_meta = ['ID', 'Nội dung hiển thị', 'Thời gian đăng', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']
        num_cols = [c for c in fb_df.columns if fb_df[c].dtype in ['float64', 'int64'] and not any(ex in c for ex in exclude_meta)]
        
        if num_cols:
            sort_m = st.sidebar.selectbox("Sắp xếp Facebook theo:", num_cols, key="sort_fb")
            fb_df = fb_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 Facebook theo {sort_m}")
            # Rút gọn tên bài viết để biểu đồ đẹp hơn
            display_df = fb_df.head(10).copy()
            display_df['ShortName'] = display_df['Nội dung hiển thị'].apply(lambda x: str(x)[:50] + "...")
            
            fig_fb = px.bar(display_df, x=sort_m, y='ShortName', orientation='h', text_auto=True, color_discrete_sequence=['#1877F2'])
            fig_fb.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_fb, use_container_width=True)
            
            st.dataframe(fb_df[['Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
    else:
        st.error("❌ Không tìm thấy file 'Facebook.csv' trên hệ thống GitHub.")

# ==========================================
# TAB 3: HIỆU QUẢ INSTAGRAM (FILE Insta.csv)
# ==========================================
with tab3:
    if ig_df is not None:
        ig_df = clean_numeric_df(ig_df)
        ig_df['Nội dung hiển thị'] = ig_df.apply(get_post_name, axis=1)
        
        exclude_meta = ['ID', 'Nội dung hiển thị', 'Thời gian đăng', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']
        num_cols = [c for c in ig_df.columns if ig_df[c].dtype in ['float64', 'int64'] and not any(ex in c for ex in exclude_meta)]
        
        if num_cols:
            sort_m = st.sidebar.selectbox("Sắp xếp Instagram theo:", num_cols, key="sort_ig")
            ig_df = ig_df.sort_values(sort_m, ascending=False)
            
            st.subheader(f"🏆 Top 10 Instagram theo {sort_m}")
            display_df = ig_df.head(10).copy()
            display_df['ShortName'] = display_df['Nội dung hiển thị'].apply(lambda x: str(x)[:50] + "...")
            
            fig_ig = px.bar(display_df, x=sort_m, y='ShortName', orientation='h', text_auto=True, color_discrete_sequence=['#E1306C'])
            fig_ig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_ig, use_container_width=True)
            
            st.dataframe(ig_df[['Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
    else:
        st.error("❌ Không tìm thấy file 'Insta.csv' trên hệ thống GitHub.")
