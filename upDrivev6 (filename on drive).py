import paramiko
import mysql.connector
import json
import requests
from openpyxl import load_workbook
from openpyxl import Workbook
import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

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
        # Tạo tên file dựa trên thời gian hiện tại
        current_time = datetime.datetime.now()
        file_name = f"data_{current_time.strftime('%d-%m-%Y')}.xlsx"
        excel_file_path = os.path.abspath(file_name)

        # Kiểm tra xem file đã tồn tại chưa
        if os.path.exists(excel_file_path):
            # Nếu file đã tồn tại, xóa nó
            os.remove(excel_file_path)

        # Tạo file mới và thêm dữ liệu vào
        workbook = Workbook()
        sheet = workbook.active

        # Ghi tiêu đề cột
        headers = [i[0] for i in cursor.description]
        sheet.append(headers)

        # Ghi dữ liệu từ MySQL vào Excel
        for row in result:
            sheet.append(row)

        # Lưu Workbook vào file Excel
        workbook.save(excel_file_path)

        # Authenticate with Google Drive using token
        gauth = GoogleAuth()
        creds_file_path = os.path.abspath("mycreds.txt")

        # Kiểm tra xem tệp mycreds.txt có tồn tại hay không
        if not os.path.exists(creds_file_path):
            # Tạo một tệp mới nếu không tồn tại
            gauth.LocalWebserverAuth()  # Creates a local webserver and handles authentication automatically
            gauth.SaveCredentialsFile(creds_file_path)  # Save the current credentials to a file

        gauth.LoadCredentialsFile(creds_file_path)  # Load saved credentials (if any)

        # ID của thư mục trên Google Drive (thay bằng ID thực tế của thư mục của bạn)
        folder_id = '189RDVanOy2-XNHxpmx0eQOH2-MYApNc1'

        # Create GoogleDrive instance with authenticated GoogleAuth instance
        drive = GoogleDrive(gauth)

        # Kiểm tra xem file đã tồn tại trên Google Drive chưa
        file_list = drive.ListFile({'q': f"title='{file_name}' and '{folder_id}' in parents and trashed=false"}).GetList()

        if file_list:
            # Nếu file đã tồn tại, cập nhật nó
            existing_file = file_list[0]
            existing_file.Delete()

        # Upload the Excel file to Google Drive vào thư mục cụ thể
        gdrive_file = drive.CreateFile({'title': file_name, 'parents': [{'id': folder_id}]})
        gdrive_file.SetContentFile(excel_file_path)
        gdrive_file.Upload()

        # Get the link to the uploaded file
        uploaded_file_link = gdrive_file['alternateLink']

        # Print the link to the uploaded file
        print(f"File uploaded to Google Drive: {uploaded_file_link}")

        # Gửi link đến file
        message = {"text": f"Dữ liệu trong bảng đã được upload lên Google Drive. [Xem file]({uploaded_file_link})"}
        requests.post(google_chat_webhook, json=message)

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
