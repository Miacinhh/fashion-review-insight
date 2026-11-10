from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="Fashion Review Insight", page_icon="🛍️", layout="wide")
st.markdown(f"<style>{(ROOT / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🛍️ Fashion Review Insight</h1><p>Phân tích đánh giá sản phẩm thời trang</p></div>', unsafe_allow_html=True)

@st.cache_data
def read_summary():
    return pd.read_csv(ROOT / "data" / "summary.csv")

all_data = read_summary()
names = sorted(all_data.product_name.unique())
chosen = st.selectbox("Chọn sản phẩm", names)
df = all_data[all_data.product_name == chosen].copy()
reviews = int(df.review_count.iloc[0])
mentions = int(df["Có đề cập"].sum())
positives = int(df["Tích cực"].sum())
negatives = int(df["Tiêu cực"].sum())
st.caption(f"{reviews} đánh giá · Dữ liệu tổng hợp từ ABSA_DATA · Mỗi đánh giá có thể đề cập nhiều khía cạnh")

buyer, seller = st.tabs(["🛒 Người mua", "📊 Người bán"])
chart = df.melt(id_vars="Khía cạnh", value_vars=["Tích cực", "Trung tính", "Tiêu cực"], var_name="Cảm xúc", value_name="Số nhãn")
fig = px.bar(chart, x="Khía cạnh", y="Số nhãn", color="Cảm xúc", barmode="group", color_discrete_map={"Tích cực":"#009b7d", "Trung tính":"#9daeb7", "Tiêu cực":"#f36b7b"})

with buyer:
    st.subheader(chosen)
    c1,c2,c3 = st.columns(3)
    c1.metric("Số đánh giá", reviews)
    c2.metric("Tỷ lệ nhãn tích cực", f"{positives / mentions:.1%}" if mentions else "—")
    c3.metric("Tỷ lệ nhãn tiêu cực", f"{negatives / mentions:.1%}" if mentions else "—")
    st.info("Tỷ lệ tính trên các khía cạnh có đề cập. Nhãn cần được kiểm duyệt độc lập trước khi dùng làm kết luận cuối cùng.")
    left,right = st.columns(2)
    with left:
        st.subheader("Điểm được khen")
        for _, row in df.sort_values("Tích cực", ascending=False).head(3).iterrows():
            st.write(f"✅ **{row['Khía cạnh']}**: {int(row['Tích cực'])} nhãn tích cực")
    with right:
        st.subheader("Điểm cần lưu ý")
        for _, row in df[df["Tiêu cực"] > 0].sort_values("Tiêu cực", ascending=False).head(3).iterrows():
            st.write(f"⚠️ **{row['Khía cạnh']}**: {int(row['Tiêu cực'])} nhãn tiêu cực")
    st.plotly_chart(fig, use_container_width=True, key="buyer_chart")

with seller:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Đánh giá", reviews)
    c2.metric("Lượt nhắc khía cạnh", mentions)
    c3.metric("Nhãn tích cực", f"{positives / mentions:.1%}" if mentions else "—")
    c4.metric("Nhãn tiêu cực", f"{negatives / mentions:.1%}" if mentions else "—")
    st.subheader("Phân bố cảm xúc theo khía cạnh")
    st.plotly_chart(fig, use_container_width=True, key="seller_chart")
    st.subheader("Ưu tiên cải thiện theo tỷ lệ tiêu cực")
    ranked = df[["Khía cạnh", "Tiêu cực", "Có đề cập", "% trong khía cạnh"]].copy()
    ranked["% trên toàn bộ nhãn"] = ranked["Tiêu cực"] / mentions * 100 if mentions else 0
    ranked = ranked.sort_values(["% trong khía cạnh", "Tiêu cực"], ascending=False)
    st.dataframe(ranked.style.format({"% trong khía cạnh":"{:.1f}%", "% trên toàn bộ nhãn":"{:.1f}%"}).set_properties(**{"text-align":"center"}), hide_index=True, use_container_width=True)
    st.caption("Mẫu số là các nhãn có đề cập (mã 1–3). Không có điểm sao hoặc ngày đánh giá trong bảng nguồn.")
