Automation Script for Data Processing and Google Drive Upload
Overview
Mã nguồn này tự động hóa quá trình thu thập dữ liệu từ một cơ sở dữ liệu MySQL qua kết nối SSH, xuất dữ liệu ra một tệp Excel và tải tệp lên Google Drive. Đồng thời, mã cũng gửi thông báo đến Google Chat.

Hướng Dẫn
Yêu Cầu Cài Đặt:

Python 3.x cài đặt.
Cài đặt các gói Python bằng lệnh: pip install paramiko mysql-connector-python openpyxl pydrive.
Cần có Google API client secret (mycreds.txt) để xác thực Google Drive. Làm theo hướng dẫn tại đây.
Cấu Hình:

Tạo một tệp config.json với cấu trúc như sau:

json
Copy code
{
    "ssh": {
        "host": "192.168.241.6",
        "port": 22,
        "username": "thaituan",
        "password": "Tuan@8999"
    },
    "mysql": {
        "host": "192.168.241.6",
        "user": "thaituan",
        "password": "Tuan@8999",
        "db": "local"
    },
    "google_chat_webhook": "https://chat.googleapis.com/v1/spaces/AAAAEXIgRyA/messages?key=YOUR_API_KEY&token=YOUR_TOKEN"
}
Sử Dụng:

Chạy mã bằng cách sử dụng lệnh: python your_script_name.py. Thay thế your_script_name.py bằng tên thực của tệp mã của bạn.
Lưu Ý:

Mã sẽ tạo một tệp Excel với tên có dấu thời gian (ví dụ: data_01-01-2023.xlsx).
Nếu tệp đã tồn tại cục bộ, nó sẽ được ghi đè.
Nếu tệp đã tồn tại trên Google Drive, nó sẽ được thay thế.