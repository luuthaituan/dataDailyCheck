import paramiko
import mysql.connector
import json
import requests
import csv
from tabulate import tabulate
import datetime

# Thông tin SSH
ssh_host = '192.168.241.6'
ssh_port = 22
ssh_username = 'thaituan'
ssh_password = 'Tuan@8999'

# Thông tin kết nối MySQL
mysql_host = '192.168.241.6'  # Địa chỉ IP của máy chủ MySQL
mysql_user = 'thaituan'
mysql_password = 'Tuan@8999'
mysql_db = 'local'

# Google Chat webhook
google_chat_webhook = 'https://chat.googleapis.com/v1/spaces/AAAAEXIgRyA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=VYNjrU3RF4Gr7yBBCNo4YJAmHQmrbeJ8xWTTWWQxw3E'

# Thông tin Confluence
confluence_url = 'https://confluence.smartosc.com/pages/viewpage.action?pageId=216402368'
confluence_username = 'tuanlt'
confluence_api_token = 'MDU0MTAxMzk5NjczOlXLw67nOG0BrWJH3ssI6nZIGTP5'

try:
    # Tạo đối tượng SSHClient
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Thực hiện kết nối SSH
    ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)

    print("Kết nối SSH thành công!")

    # Tạo kênh chuyển tiếp SSH
    ssh_channel = ssh.get_transport().open_channel('direct-tcpip', (mysql_host, 3306), ('127.0.0.1', 0))

    # Lấy địa chỉ cổng local
    local_port = ssh_channel.getpeername()[1]

    # Kết nối MySQL qua SSH
    mysql_conn = mysql.connector.connect(
        host='192.168.241.6',
        port=3306,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db
    )

    print("Kết nối MySQL qua SSH thành công!")

    # Thực hiện truy vấn SQL
    select_query1 = "SELECT * FROM local.test"
    cursor = mysql_conn.cursor()
    cursor.execute(select_query1)
    result = cursor.fetchall()

    # Kiểm tra và xuất thông báo
    if not result:
        # Gửi thông báo không có dữ liệu
        message = {"text": "Query Monitor Order TW stuck tại pending_payment [Chạy daily] => Không có data"}
        requests.post(google_chat_webhook, json=message)
    else:
        # Tạo nội dung bảng từ dữ liệu
        headers = [i[0] for i in cursor.description]
        table = tabulate(result, headers, tablefmt="grid", disable_numparse=True)

        # Tạo tên file dựa trên thời gian hiện tại
        current_time = datetime.datetime.now()
        file_name = f"data_{current_time.strftime('%d-%m-%Y')}.csv"

        # Ghi dữ liệu vào file CSV
        csv_file_path = f'./{file_name}'
        with open(csv_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(headers)
            csv_writer.writerows(result)

        # Gửi nội dung bảng
        message = {"text": f"Dữ liệu trong bảng:\n```\n{table}\n```"}
        requests.post(google_chat_webhook, json=message)

        # Đọc nội dung từ file CSV
        with open(csv_file_path, 'r') as file:
            csv_content = file.read()

        # Tạo tiêu đề và mô tả trong định dạng cần thiết cho REST API
        page_title = f'Data Report - {current_time.strftime("%d-%m-%Y")}'
        page_description = f'Data report generated at {current_time.strftime("%H:%M:%S")}'

        # Tạo tiêu đề và mô tả trong định dạng cần thiết cho REST API
        page_data = {
            'title': page_title,
            'type': 'page',
            'body': {
                'storage': {
                    'value': page_description,
                    'representation': 'storage',
                },
            },
        }

        # Cấu hình header cho REST API request
        headers = {
            'Content-Type': 'application/json',
        }

        # Xây dựng REST API request để tạo trang mới hoặc cập nhật trang hiện tại
        response = requests.put(
            confluence_url,
            auth=(confluence_username, confluence_api_token),
            headers=headers,
            json=page_data
        )

        # Kiểm tra kết quả
        if response.status_code == 200:
            print('Cập nhật trang thành công!')
        else:
            print(f'Lỗi: {response.status_code} - {response.text}')

except paramiko.AuthenticationException:
    print("Lỗi xác thực: Sai tên đăng nhập hoặc mật khẩu.")
except paramiko.SSHException as e:
    print(f"Lỗi kết nối SSH: {str(e)}")
except mysql.connector.Error as err:
    print(f"Lỗi MySQL: {err}")
except Exception as e:
    print(f"Lỗi không xác định: {str(e)}")

finally:
    # Đóng kết nối MySQL
    if 'mysql_conn' in locals():
        mysql_conn.close()

    # Đóng kết nối SSH sau khi kết thúc công việc
    if ssh.get_transport() is not None:
        ssh.get_transport().close()
