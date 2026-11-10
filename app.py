"""Public classroom demo. Charts use model predictions, not hand-labelled columns."""

import pandas as pd
import plotly.express as px
import streamlit as st

from model import ASPECTS, LABELS, load_model, predict

st.set_page_config(page_title="Fashion Review Insight · ViSoBERT", page_icon="🛍️", layout="wide")
st.title("🛍️ Fashion Review Insight")
st.caption("Dự đoán ABSA bằng mô hình ViSoBERT đã fine-tune của nhóm · 5 khía cạnh")

repo_id = "dkkdje/fashion-review-visobert"
token = None


@st.cache_resource(show_spinner="Đang nạp mô hình ViSoBERT...")
def cached_model(model_repo_id, model_token):
    return load_model(model_repo_id, model_token)


@st.cache_data(show_spinner=False)
def parse_file(blob, filename):
    import io
    stream = io.BytesIO(blob)
    if filename.lower().endswith(".csv"):
        return pd.read_csv(stream)
    return pd.read_excel(stream)


def add_predictions(frame, tokenizer, model):
    frame = frame.copy()
    ids, scores = predict(frame["review_text"].astype(str).tolist(), tokenizer, model)
    for index, aspect in enumerate(ASPECTS):
        frame[f"pred_{aspect}"] = ids[:, index]
        frame[f"confidence_{aspect}"] = scores[:, index]
    return frame


def summary(frame):
    rows = []
    for aspect in ASPECTS:
        counts = frame[f"pred_{aspect}"].value_counts()
        mentioned = sum(int(counts.get(label, 0)) for label in (1, 2, 3))
        negative = int(counts.get(1, 0))
        rows.append({
            "Khía cạnh": aspect,
            "Không đề cập": int(counts.get(0, 0)),
            "Tiêu cực": negative,
            "Trung tính": int(counts.get(2, 0)),
            "Tích cực": int(counts.get(3, 0)),
            "Có đề cập": mentioned,
            "% tiêu cực trong khía cạnh": 100 * negative / mentioned if mentioned else 0,
            "% tiêu cực trên toàn bộ review": 100 * negative / len(frame) if len(frame) else 0,
        })
    return pd.DataFrame(rows)


try:
    tokenizer, model = cached_model(repo_id, token)
except Exception as exc:
    st.error(f"Chưa nạp được mô hình: {exc}")
    st.stop()

buyer, seller = st.tabs(["🛒 Người mua", "📊 Người bán"])

with buyer:
    st.subheader("Thử dự đoán một đánh giá mới")
    review = st.text_area("Nhập nội dung review", placeholder="Ví dụ: Áo đẹp và vừa vặn nhưng giao hàng chậm.")
    if st.button("Dự đoán", type="primary"):
        if not review.strip():
            st.warning("Hãy nhập nội dung đánh giá.")
        else:
            ids, scores = predict([review], tokenizer, model)
            st.dataframe(pd.DataFrame({
                "Khía cạnh": ASPECTS,
                "Dự đoán": [LABELS[int(x)] for x in ids[0]],
                "Độ tin cậy": [f"{x:.1%}" for x in scores[0]],
            }), hide_index=True, use_container_width=True)

with seller:
    st.subheader("Phân tích review bằng mô hình")
    uploaded = st.file_uploader("Tải dữ liệu review CSV hoặc Excel", type=["csv", "xlsx"])
    if uploaded is None:
        st.info("Tải file 230 review để mô hình dự đoán và tạo biểu đồ. Nhãn gốc chỉ dùng để đối chiếu nếu có.")
    else:
        data = parse_file(uploaded.getvalue(), uploaded.name)
        required = {"review_text", "product_name"}
        missing = required - set(data.columns)
        if missing:
            st.error("Thiếu cột: " + ", ".join(sorted(missing)))
        else:
            data = data.dropna(subset=["review_text", "product_name"]).copy()
            data = data[data["review_text"].astype(str).str.strip().ne("")]
            if data.empty:
                st.warning("File không có review hợp lệ.")
            elif len(data) > 230:
                st.warning("Bản demo giới hạn tối đa 230 review mỗi lần tải.")
            else:
                file_key = (uploaded.name, len(uploaded.getvalue()), hash(uploaded.getvalue()))
                if st.session_state.get("predicted_file_key") != file_key:
                    st.session_state.pop("predicted", None)
                if st.button(f"Chạy ViSoBERT cho {len(data)} review", type="primary"):
                    with st.spinner("Mô hình đang dự đoán từng review..."):
                        st.session_state.predicted = add_predictions(data, tokenizer, model)
                        st.session_state.predicted_file_key = file_key
                predicted = st.session_state.get("predicted")
                if predicted is not None:
                    selected = st.selectbox("Chọn sản phẩm", sorted(predicted["product_name"].unique()))
                    subset = predicted[predicted["product_name"] == selected]
                    result = summary(subset)
                    st.metric("Số review đã dự đoán", len(subset))
                    long = result.melt(
                        id_vars="Khía cạnh", value_vars=["Tích cực", "Trung tính", "Tiêu cực"],
                        var_name="Cảm xúc", value_name="Số dự đoán",
                    )
                    chart = px.bar(long, x="Khía cạnh", y="Số dự đoán", color="Cảm xúc", barmode="group")
                    st.plotly_chart(chart, use_container_width=True, key="seller_prediction_chart")
                    st.subheader("Ưu tiên cải thiện")
                    result = result.sort_values("% tiêu cực trong khía cạnh", ascending=False)
                    st.dataframe(result, hide_index=True, use_container_width=True)
                    st.caption("Tất cả biểu đồ và tỷ lệ trên đây tính từ dự đoán ViSoBERT. Mã 0 không được tính là lượt đề cập.")
                    if all(aspect in subset.columns for aspect in ASPECTS):
                        st.subheader("Đối chiếu với nhãn gốc")
                        comparison = []
                        for aspect in ASPECTS:
                            truth = pd.to_numeric(subset[aspect], errors="coerce")
                            valid = truth.isin([0, 1, 2, 3])
                            count = int(valid.sum())
                            correct = int((truth[valid] == subset.loc[valid, f"pred_{aspect}"]).sum())
                            comparison.append({
                                "Khía cạnh": aspect,
                                "Số review có nhãn": count,
                                "Dự đoán trùng nhãn gốc": correct,
                                "Tỷ lệ trùng": f"{correct / count:.1%}" if count else "—",
                            })
                        st.dataframe(pd.DataFrame(comparison), hide_index=True, use_container_width=True)
                        st.caption("Đối chiếu chỉ áp dụng cho file đang tải lên; không phải kết quả test nội bộ 8.892 review trong notebook.")
                    st.download_button("Tải kết quả dự đoán", predicted.to_csv(index=False).encode("utf-8-sig"), "visobert_predictions.csv", "text/csv")
