import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Click Studio - Dashboard v4.5", page_icon="📈", layout="wide")
st.title("📈 Dashboard Phân Tích: Facebook & Instagram")

# ==========================================
# ⚙️ KHU VỰC CẤU HÌNH (TÙY CHỈNH TẠI ĐÂY)
# ==========================================

# 1. DANH SÁCH ẨN CỘT
FB_COLS_TO_HIDE = [
    "Thời lượng (giây)_x", 
    "Thời lượng (giây)_y",
    "Nhãn tùy chỉnh",
    "Trạng thái nội dung"
]

IG_COLS_TO_HIDE = [
    "ID bài viết",
    "ID tài khoản",
    "Tên tài khoản",
    "Bình luận về dữ liệu"
]

# 2. DANH SÁCH THỨ TỰ CỘT HIỂN THỊ
FB_COLUMN_ORDER = [
    "Thời gian đăng",
    "Nội dung hiển thị",
    "Số người tiếp cận",
    "Lượt xem",
    "Cảm xúc, bình luận và lượt chia sẻ",
    "Cảm xúc",
    "Bình luận",
    "Lượt chia sẻ",
    "Tổng lượt click",
    "Lượt click khác",
    "Số Giây xem",
    "Số Giây xem trung bình"
]

IG_COLUMN_ORDER = [
    "Thời gian đăng",
    "Nội dung hiển thị",
    "Lượt thích",
    "Lượt xem",
    "Số người tiếp cận",
    "Lượt chia sẻ",
    "Lượt theo dõi",
    "Bình luận",
    "Lượt lưu",
    "Thời lượng (giây)",
    "Loại bài viết"
]
# ==========================================

# --- HÀM ĐỌC FILE ---
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
        if not any(ex in col for ex in
