import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Dashboard v4.1", page_icon="📈", layout="wide")
st.title("📈 Dashboard Phân Tích: Facebook & Instagram")

# ==========================================
# ⚙️ KHU VỰC CẤU HÌNH (TÙY CHỈNH TẠI ĐÂY)
# ==========================================
# Bạn hãy copy chính xác tên cột muốn ẨN và dán vào giữa hai dấu ngoặc kép, cách nhau bởi dấu phẩy.
# Ví dụ: ["Cảm xúc", "Lượt lưu", "Ngôn ngữ"]

FB_COLS_TO_HIDE = [
    "Thời lượng (giây)",
    "Nhãn tùy chỉnh",
    "Trạng thái nội dung được tài trợ",
    "Ngôn ngữ", 
    "Thu nhập ước tính ((USD))",
    "CPM quảng cáo ((USD))",
    "Lượt hiển thị quảng cáo",
    "Lượt click vào liên kết",
    "Tổng số lượt click của người dùng khớp với đối tượng nhắm mục tiêu (Photo Click)",
    "Bình luận về dữ liệu",
    # Thêm các cột Facebook muốn ẩn vào đây...
]

IG_COLS_TO_HIDE = [
    "ID",
    "Bình luận về dữ liệu",
    # Thêm các cột Instagram muốn ẩn vào đây...
]

# ==========================================

# --- HÀM ĐỌC FILE V4.0 (VƯỢT LỖI PARSER ERROR) ---
@st.cache_data
def load_csv_smart(file_path):
    for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                line1 = f.readline()
                line2 = f.readline()
            
            skip_n = 0
            if 'sep=' in line1.lower():
                if ',' not in line2 and '\t' not in line2: skip_n = 2
                else: skip_n = 1
            
            df = pd.read_csv(file_path, encoding=enc, skiprows=skip_n)
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except Exception: continue
    return None

def get_post_name(row):
    for col in ["Tiêu đề", "Mô tả", "Nội dung", "Liên kết vĩnh viễn"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])
    return "Nội dung không có tiêu đề"

def clean_numeric_df(df):
    exclude = ['ID', 'Ngày', 'Thời gian đăng', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Nội dung hiển thị']
    for col in df.columns:
        if not any(ex in col for ex in exclude) and df[col].dtype == 'object':
            try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
            except: pass
    return df

# --- BỘ TỪ ĐIỂN MAP TÊN FILE ---
file_mapping = {
    "luot_click_vao_lien_ket.csv": "Lượt click vào liên kết",
    "luot_theo_doi.csv": "Lượt theo dõi",
    "luot_truy_cap.csv": "Lượt truy cập",
    "luot_tuong_tac.csv": "Lượt tương tác",
    "luot_xem.csv": "Lượt xem",
    "nguoi_xem.csv": "Người xem"
}
target_page_files_lower = list(file_mapping.keys())

# --- QUÉT FILE HỆ THỐNG ---
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
    for file_lower, display_name in file_mapping.items():
        if any(f.lower() == file_lower for f in all_files): st.caption(f"✅ {display_name}")
        else: st.caption(f"❌ Thiếu: {file_lower}")
    st.markdown("---")

# --- PHÂN LOẠI DỮ LIỆU ---
page_dfs = []
fb_df = load_csv_smart(fb_file) if fb_file else None
ig_df = load_csv_smart(ig_file) if ig_file else None

for f_name in all_files:
    f_lower = f_name.lower()
    if f_lower in target_page_files_lower:
        df_temp = load_csv_smart(f_name)
        if df_temp is not None and not df_temp.empty:
            date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
            if date_col:
                df_temp = df_temp.rename(columns={date_col: 'Ngày'})
                metric_name = file_mapping[f_lower]
                
                if "Primary" in df_temp.columns:
                    df_temp = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric_name})
                    page_dfs.append(df_temp)
                else:
                    num_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                    if num_cols:
                        df_temp = df_temp[['Ngày', num_cols[0]]].rename(columns={num_cols[0]: metric_name})
                        page_dfs.append(df_temp)

# --- GIAO DIỆN CHÍNH ---
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan Trang", "📘 Hiệu quả Facebook", "📸 Hiệu quả Instagram"])

with tab1:
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
        else: st.warning("Không có cột dữ liệu số nào để hiển thị.")
    else: st.warning("Chưa có dữ liệu Tổng quan.")

with tab2:
    if fb_df is not None:
        fb_df = clean_numeric_df(fb_df)
        fb_df['Nội dung hiển thị'] = fb_df.apply(get_post_name, axis=1)
        
        # Lọc bỏ các cột nằm trong danh sách ẨN
        cols_to_drop = [c for c in FB_COLS_TO_HIDE if c in fb_df.columns]
        display_fb_df = fb_df.drop(columns=cols_to_drop)
        
        # Chỉ lấy những cột số còn lại (không bị ẩn) để làm tùy chọn sắp xếp
        num_cols = [c for c in display_fb_df.columns if display_fb_df[c].dtype in ['float64', 'int64'] and 'ID' not in c]
        
        if num_cols:
            sort_fb = st.sidebar.selectbox("Sắp xếp Facebook theo:", num_cols, key="sb_fb")
            display_fb_df = display_fb_df.sort_values(sort_fb, ascending=False)
            
            st.subheader(f"🏆 Top 10 Facebook ({sort_fb})")
            fig_fb = px.bar(display_fb_df.head(10), x=sort_fb, y=display_fb_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2'])
            fig_fb.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
            st.plotly_chart(fig_fb, use_container_width=True)
            
            # Hiển thị bảng dữ liệu đã được dọn dẹp
            st.dataframe(display_fb_df[['Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
        else: st.warning("Không tìm thấy các cột số liệu tương tác.")
    else: st.error("Chưa tải dữ liệu Facebook lên.")

with tab3:
    if ig_df is not None:
        ig_df = clean_numeric_df(ig_df)
        ig_df['Nội dung hiển thị'] = ig_df.apply(get_post_name, axis=1)
        
        # Lọc bỏ các cột nằm trong danh sách ẨN
        cols_to_drop = [c for c in IG_COLS_TO_HIDE if c in ig_df.columns]
        display_ig_df = ig_df.drop(columns=cols_to_drop)
        
        num_cols = [c for c in display_ig_df.columns if display_ig_df[c].dtype in ['float64', 'int64'] and 'ID' not in c]
        
        if num_cols:
            sort_ig = st.sidebar.selectbox("Sắp xếp Instagram theo:", num_cols, key="sb_ig")
            display_ig_df = display_ig_df.sort_values(sort_ig, ascending=False)
            
            st.subheader(f"🏆 Top 10 Instagram ({sort_ig})")
            fig_ig = px.bar(display_ig_df.head(10), x=sort_ig, y=display_ig_df.head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C'])
            fig_ig.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''})
            st.plotly_chart(fig_ig, use_container_width=True)
            
            # Hiển thị bảng dữ liệu đã được dọn dẹp
            st.dataframe(display_ig_df[['Thời gian đăng', 'Nội dung hiển thị'] + num_cols])
        else: st.warning("Không tìm thấy các cột số liệu tương tác.")
    else: st.error("Chưa tải dữ liệu Instagram lên.")
