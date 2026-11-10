# Fashion Review Insight · ViSoBERT demo

Web Streamlit dự đoán ABSA thật bằng checkpoint của nhóm. Tập 230 review được người dùng tải lên lúc chạy; nhãn gốc không được dùng để tính biểu đồ dự đoán.

## Cấu hình mô hình

- Tại máy: đặt `best_visobert_multiaspect.pt` cạnh `app.py`.
- Trên Streamlit Cloud: app tải checkpoint từ kho mô hình công khai `dkkdje/fashion-review-visobert`. Không cần token hay Streamlit Secrets.
- Giữ checkpoint ngoài GitHub thường vì file vượt giới hạn 100 MiB.

## Chạy tại máy

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

File dữ liệu tải lên cần các cột `review_text`, `product_name`. Nếu có nhãn gốc `Chất liệu`, `Kiểu dáng`, `Kích cỡ`, `Giá cả`, `Dịch vụ`, chúng chỉ dùng để đối chiếu riêng, không dùng để tạo biểu đồ dự đoán.

Mô hình theo notebook: `uitnlp/visobert`, tối đa 192 token, năm đầu phân loại, nhãn 0–3 theo thứ tự không đề cập/tiêu cực/trung tính/tích cực.
