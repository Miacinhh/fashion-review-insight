# Fashion Review Insight

Dashboard Streamlit dùng số liệu **tổng hợp** từ 230 đánh giá trong [bảng ABSA_DATA](https://docs.google.com/spreadsheets/d/1WZ03ywEOuyh-nAntkJ7cxT_aHxyUtmxeKEt8mrtsfKo/edit?gid=1763109722). Repository công khai này không chứa văn bản đánh giá gốc hoặc mã đánh giá từng người dùng.

Chạy: `pip install -r requirements.txt` rồi `streamlit run app.py`.

Mã khía cạnh gốc: 0 = không đề cập, 1 = tiêu cực, 2 = trung tính, 3 = tích cực. Tỷ lệ tính trên các lượt nhắc khía cạnh (mã 1–3), không phải trên số bài đánh giá. Nhãn cần được kiểm duyệt độc lập trước khi dùng làm kết luận cuối cùng.
