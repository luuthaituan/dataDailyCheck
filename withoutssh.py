import mysql.connector
import json
import requests

# Thông tin kết nối MySQL
mysql_host = '192.168.10.146'  # Địa chỉ IP của máy chủ MySQL
mysql_port = 30003  # Cổng MySQL
mysql_user = 'vt2pniqibrqv6_ro'
mysql_password = 'FhMMJTrLejNYax3'
mysql_db = 'vt2pniqibrqv6'

# Google Chat webhook
google_chat_webhook = 'https://chat.googleapis.com/v1/spaces/AAAAEXIgRyA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=VYNjrU3RF4Gr7yBBCNo4YJAmHQmrbeJ8xWTTWWQxw3E'

try:
    # Kết nối MySQL
    mysql_conn = mysql.connector.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db
    )

    print("Kết nối MySQL thành công!")

    # Thực hiện truy vấn SQL
    select_query = input("Nhập truy vấn của bạn: ")
    cursor = mysql_conn.cursor()
    cursor.execute(select_query)
    result = cursor.fetchall()

    # Kiểm tra và xuất thông báo
    if not result:
        # Gửi thông báo không có dữ liệu
        message = {"text": "Không có dữ liệu trong bảng."}
        requests.post(google_chat_webhook, json=message)
    else:
        # Gửi dữ liệu dưới dạng JSON
        message = {"text": "Dữ liệu trong bảng:\n" + json.dumps(result, indent=2)}
        requests.post(google_chat_webhook, json=message)

except mysql.connector.Error as err:
    print(f"Lỗi MySQL: {err}")
except Exception as e:
    print(f"Lỗi không xác định: {str(e)}")

finally:
    # Đóng kết nối MySQL
    if 'mysql_conn' in locals():
        mysql_conn.close()
