import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Click Studio - Dashboard v6.2", page_icon="📈", layout="wide")
st.markdown("<h1 style='text-align: center;'>📈 Dashboard Phân Tích: Facebook & Instagram</h1>", unsafe_allow_html=True)

# ==========================================
# ⚙️ KHU VỰC CẤU HÌNH
# ==========================================
FB_COLS_TO_HIDE = ["Thời lượng (giây)_x", "Thời lượng (giây)_y", "Nhãn tùy chỉnh", "Trạng thái nội dung"]
IG_COLS_TO_HIDE = ["ID bài viết", "ID tài khoản", "Tên tài khoản", "Bình luận về dữ liệu"]

FB_COLUMN_ORDER = [
    "Thời gian đăng", "Nội dung hiển thị", "Số người tiếp cận", "Lượt xem",
    "Cảm xúc, bình luận và lượt chia sẻ", "Cảm xúc", "Bình luận", "Lượt chia sẻ",
    "Tổng lượt click", "Lượt click khác", "Số Giây xem", "Số Giây xem trung bình"
]

IG_COLUMN_ORDER = [
    "Thời gian đăng", "Nội dung hiển thị", "Lượt thích", "Lượt xem",
    "Số người tiếp cận", "Lượt chia sẻ", "Lượt theo dõi", "Bình luận",
    "Lượt lưu", "Thời lượng (giây)", "Loại bài viết"
]

overview_keywords = {
    "luot_click": "Lượt click",
    "luot_theo_doi": "Lượt theo dõi",
    "luot_truy_cap": "Lượt truy cập",
    "luot_tuong_tac": "Lượt tương tác",
    "luot_xem": "Lượt xem",
    "nguoi_xem": "Người xem",
    "so_nguoi_tiep_can": "Số người tiếp cận"
}

# --- HÀM ĐỌC FILE ---
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
            text = str(row[col]).strip()
            lines = [line.strip() for line in text.splitlines() if line.strip() != ""]
            if lines: return lines[0]
    return "Nội dung không có tiêu đề"

def clean_numeric_df(df):
    exclude = ['ID', 'Ngày', 'Thời gian đăng', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Nội dung hiển thị']
    for col in df.columns:
        if not any(ex in col for ex in exclude) and df[col].dtype == 'object':
            try: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
            except: pass
    return df

def merge_overview_dfs(dfs):
    if not dfs: return None, []
    valid_dfs_agg = []
    for df in dfs:
        df['Ngày'] = pd.to_datetime(df['Ngày'], errors='coerce').dt.normalize()
        df = df.dropna(subset=['Ngày'])
        cols = [c for c in df.columns if c != 'Ngày']
        for c in cols:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        df_agg = df.groupby('Ngày')[cols].sum().reset_index()
        valid_dfs_agg.append(df_agg)
    if not valid_dfs_agg: return None, []
    merged = valid_dfs_agg[0]
    for next_df in valid_dfs_agg[1:]: 
        merged = pd.merge(merged, next_df, on="Ngày", how="outer")
    merged = merged.fillna(0).sort_values('Ngày', ascending=False)
    metrics = [c for c in merged.columns if c != 'Ngày']
    return merged, metrics

# --- 1. ĐỌC VÀ LÀM SẠCH DỮ LIỆU ---
all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
fb_file = next((f for f in all_files if f.lower() in ['facebook.csv', 'fb.csv']), None)
ig_file = next((f for f in all_files if f.lower() in ['insta.csv', 'instagram.csv', 'ig.csv']), None)

fb_page_dfs, ig_page_dfs = [], []

for f_name in all_files:
    if f_name in [fb_file, ig_file]: continue
    f_lower = f_name.lower()
    metric_name = None
    for key, disp in overview_keywords.items():
        if key in f_lower: metric_name = disp; break
    if metric_name:
        df_temp = load_csv_smart(f_name)
        if df_temp is not None and not df_temp.empty:
            date_col = next((c for c in df_temp.columns if 'ngày' in c.lower() or 'date' in c.lower()), None)
            if date_col:
                df_temp = df_temp.rename(columns={date_col: 'Ngày'})
                if "Primary" in df_temp.columns: df_target = df_temp[['Ngày', 'Primary']].rename(columns={"Primary": metric_name})
                else:
                    num_cols = [c for c in df_temp.select_dtypes(include=['number']).columns if 'ID' not in c]
                    df_target = df_temp[['Ngày', num_cols[0]]].rename(columns={num_cols[0]: metric_name}) if num_cols else None
                if df_target is not None:
                    is_ig = False
                    if f_lower.startswith('ig_') or f_lower.startswith('insta_'): is_ig = True
                    else:
                        for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
                            try:
                                with open(f_name, 'r', encoding=enc) as f:
                                    if 'instagram' in f.read(200).lower(): is_ig = True; break
                            except: pass
                    if is_ig: ig_page_dfs.append(df_target)
                    else: fb_page_dfs.append(df_target)

merged_fb_overview, metrics_fb_overview = merge_overview_dfs(fb_page_dfs)
merged_ig_overview, metrics_ig_overview = merge_overview_dfs(ig_page_dfs)

# XỬ LÝ BÀI VIẾT FB/IG
display_fb_df = None
if fb_file:
    fb_df = load_csv_smart(fb_file)
    if fb_df is not None:
        fb_df = clean_numeric_df(fb_df); fb_df['Nội dung hiển thị'] = fb_df.apply(get_post_name, axis=1)
        display_fb_df = fb_df.drop(columns=[c for c in FB_COLS_TO_HIDE if c in fb_df.columns])
        exist_fb = [c for c in FB_COLUMN_ORDER if c in display_fb_df.columns]
        rem_fb = [c for c in display_fb_df.columns if c not in exist_fb and c not in ['ID', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']]
        display_fb_df = display_fb_df[exist_fb + rem_fb].iloc[:, :15]

display_ig_df = None
if ig_file:
    ig_df = load_csv_smart(ig_file)
    if ig_df is not None:
        ig_df = clean_numeric_df(ig_df); ig_df['Nội dung hiển thị'] = ig_df.apply(get_post_name, axis=1)
        display_ig_df = ig_df.drop(columns=[c for c in IG_COLS_TO_HIDE if c in ig_df.columns])
        exist_ig = [c for c in IG_COLUMN_ORDER if c in display_ig_df.columns]
        rem_ig = [c for c in display_ig_df.columns if c not in exist_ig and c not in ['ID', 'Ngày', 'Liên kết vĩnh viễn', 'Tiêu đề', 'Mô tả', 'Tên Trang', 'Tên người dùng tài khoản']]
        display_ig_df = display_ig_df[exist_ig + rem_ig]

# --- 2. THỜI GIAN & CHỈ SỐ TỔNG ---
min_dates, max_dates = [], []
for df in [merged_fb_overview, merged_ig_overview]:
    if df is not None: min_dates.append(df['Ngày'].min()); max_dates.append(df['Ngày'].max())

date_subtitle = ""
if min_dates and max_dates:
    min_date, max_date = min(min_dates).strftime('%d/%m/%Y'), max(max_dates).strftime('%d/%m/%Y')
    date_subtitle = f"📅 Thời gian báo cáo: {min_date} ➔ {max_date}"
    st.markdown(f"<h4 style='text-align: center; color: #555; margin-top: -15px; padding-bottom: 20px;'>{date_subtitle}</h4>", unsafe_allow_html=True)

# --- 3. SIDEBAR & BIỂU ĐỒ ---
with st.sidebar:
    st.header("🔄 Điều khiển")
    if st.button("🚀 Cập nhật dữ liệu mới"): st.cache_data.clear(); st.rerun()
    st.markdown("---")
    st.header("⚙️ Xếp hạng & Chỉ số")
    sel_fb_ov = st.multiselect("Chỉ số T.Quan FB:", metrics_fb_overview, default=metrics_fb_overview[:2] if len(metrics_fb_overview)>1 else metrics_fb_overview) if metrics_fb_overview else []
    sel_ig_ov = st.multiselect("Chỉ số T.Quan IG:", metrics_ig_overview, default=metrics_ig_overview[:2] if len(metrics_ig_overview)>1 else metrics_ig_overview) if metrics_ig_overview else []
    sort_fb = st.selectbox("Xếp hạng bài viết FB theo:", [c for c in display_fb_df.columns if display_fb_df[c].dtype in ['float64', 'int64']], key="sb_fb") if display_fb_df is not None else None
    sort_ig = st.selectbox("Xếp hạng bài viết IG theo:", [c for c in display_ig_df.columns if display_ig_df[c].dtype in ['float64', 'int64']], key="sb_ig") if display_ig_df is not None else None

def get_fig(df, selected):
    if df is not None and selected:
        fig = px.line(df.sort_values('Ngày'), x='Ngày', y=selected, markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
        fig.update_xaxes(type='date', title='Thời gian'); return fig
    return None

fig_fb_ov, fig_ig_ov = get_fig(merged_fb_overview, sel_fb_ov), get_fig(merged_ig_overview, sel_ig_ov)
fig_fb = px.bar(display_fb_df.sort_values(sort_fb, ascending=False).head(10), x=sort_fb, y=display_fb_df.sort_values(sort_fb, ascending=False).head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#1877F2']).update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}) if display_fb_df is not None and sort_fb else None
fig_ig = px.bar(display_ig_df.sort_values(sort_ig, ascending=False).head(10), x=sort_ig, y=display_ig_df.sort_values(sort_ig, ascending=False).head(10)['Nội dung hiển thị'].apply(lambda x: str(x)[:50]+"..."), orientation='h', text_auto=True, color_discrete_sequence=['#E1306C']).update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}) if display_ig_df is not None and sort_ig else None

# --- HÀM HIỂN THỊ METRICS ---
def render_metrics(df):
    c1, c2, c3 = st.columns(3)
    val_f = f"{int(df['Lượt theo dõi'].sum()):,}" if 'Lượt theo dõi' in df.columns else "0"
    val_v = f"{int(df['Lượt xem'].sum()):,}" if 'Lượt xem' in df.columns else "0"
    val_i = f"{int(df['Lượt tương tác'].sum()):,}" if 'Lượt tương tác' in df.columns else "0"
    c1.metric("Tổng Follower mới", val_f); c2.metric("Tổng Lượt xem", val_v); c3.metric("Tổng Lượt tương tác", val_i)

def get_metrics_html(df):
    val_f = f"{int(df['Lượt theo dõi'].sum()):,}" if 'Lượt theo dõi' in df.columns else "0"
    val_v = f"{int(df['Lượt xem'].sum()):,}" if 'Lượt xem' in df.columns else "0"
    val_i = f"{int(df['Lượt tương tác'].sum()):,}" if 'Lượt tương tác' in df.columns else "0"
    return f"""
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
        <div style="flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; margin-right: 10px; border: 1px solid #ddd;">
            <div style="font-size: 12px; color: #666;">Tổng Follower mới</div>
            <div style="font-size: 20px; font-weight: bold; color: #1877F2;">{val_f}</div>
        </div>
        <div style="flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; margin-right: 10px; border: 1px solid #ddd;">
            <div style="font-size: 12px; color: #666;">Tổng Lượt xem</div>
            <div style="font-size: 20px; font-weight: bold; color: #1877F2;">{val_v}</div>
        </div>
        <div style="flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ddd;">
            <div style="font-size: 12px; color: #666;">Tổng Lượt tương tác</div>
            <div style="font-size: 20px; font-weight: bold; color: #1877F2;">{val_i}</div>
        </div>
    </div>
    """

# --- 4. XUẤT PDF ---
with st.sidebar:
    st.markdown("---"); st.header("🖨️ Xuất Báo Cáo PDF")
    if st.button("📥 TẢI XUỐNG FILE PDF", type="primary", use_container_width=True):
        st.info("⏳ Đang kết xuất PDF, vui lòng chờ khoảng 3 giây...")
        pdf_html = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8">
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
        <style>
            body {{ font-family: Arial; background: white; }}
            #report-container {{ width: 1100px; padding: 20px; }}
            h1 {{ text-align: center; color: #1877F2; }}
            .date-subtitle {{ text-align: center; color: #666; font-weight: bold; margin-bottom: 30px; }}
            h2 {{ border-bottom: 2px solid #1877F2; color: #333; margin-top: 40px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
            th, td {{ border: 1px solid #ddd; padding: 6px; }}
            th {{ background: #f4f4f4; }}
        </style></head><body><div id="report-container">
            <h1>📊 BÁO CÁO DỮ LIỆU: CLICK STUDIO</h1><p class="date-subtitle">{date_subtitle}</p>
        """
        if merged_fb_overview is not None:
            pdf_html += f"<h2>1. TỔNG QUAN FACEBOOK</h2>{get_metrics_html(merged_fb_overview)}"
            if fig_fb_ov: pdf_html += fig_fb_ov.to_html(full_html=False, include_plotlyjs=False)
            pdf_html += merged_fb_overview.assign(Ngày=merged_fb_overview['Ngày'].dt.strftime('%d/%m/%Y')).to_html(index=False)
        if merged_ig_overview is not None:
            pdf_html += f"<h2>2. TỔNG QUAN INSTAGRAM</h2>{get_metrics_html(merged_ig_overview)}"
            if fig_ig_ov: pdf_html += fig_ig_ov.to_html(full_html=False, include_plotlyjs=False)
            pdf_html += merged_ig_overview.assign(Ngày=merged_ig_overview['Ngày'].dt.strftime('%d/%m/%Y')).to_html(index=False)
        if display_fb_df is not None:
            pdf_html += f"<h2>3. BÀI VIẾT FACEBOOK (Top {sort_fb})</h2>"
            if fig_fb: pdf_html += fig_fb.to_html(full_html=False, include_plotlyjs=False)
            pdf_html += display_fb_df.sort_values(sort_fb, ascending=False).head(20).to_html(index=False)
        if display_ig_df is not None:
            pdf_html += f"<h2>4. BÀI VIẾT INSTAGRAM (Top {sort_ig})</h2>"
            if fig_ig: pdf_html += fig_ig.to_html(full_html=False, include_plotlyjs=False)
            pdf_html += display_ig_df.sort_values(sort_ig, ascending=False).head(20).to_html(index=False)
        pdf_html += """</div><script>setTimeout(() => {
            html2pdf().set({margin:0.4, filename:'Bao_Cao_Click_Studio.pdf', html2canvas:{scale:2}, jsPDF:{format:'a4', orientation:'landscape'}})
            .from(document.getElementById('report-container')).save();
        }, 2500);</script></body></html>"""
        components.html(pdf_html, height=120)

# --- 5. GIAO DIỆN WEB (4 TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng quan FB", "📸 Tổng quan IG", "📘 Bài viết FB", "📸 Bài viết IG"])
with tab1:
    if merged_fb_overview is not None:
        render_metrics(merged_fb_overview)
        if fig_fb_ov: st.plotly_chart(fig_fb_ov, use_container_width=True)
        st.dataframe(merged_fb_overview.assign(Ngày=merged_fb_overview['Ngày'].dt.strftime('%d/%m/%Y')))
with tab2:
    if merged_ig_overview is not None:
        render_metrics(merged_ig_overview)
        if fig_ig_ov: st.plotly_chart(fig_ig_ov, use_container_width=True)
        st.dataframe(merged_ig_overview.assign(Ngày=merged_ig_overview['Ngày'].dt.strftime('%d/%m/%Y')))
with tab3:
    if display_fb_df is not None:
        if fig_fb: st.plotly_chart(fig_fb, use_container_width=True)
        st.dataframe(display_fb_df.sort_values(sort_fb, ascending=False))
with tab4:
    if display_ig_df is not None:
        if fig_ig: st.plotly_chart(fig_ig, use_container_width=True)
        st.dataframe(display_ig_df.sort_values(sort_ig, ascending=False))
