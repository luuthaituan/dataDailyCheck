import datetime
import logging
import os

import pandas as pd
import pymysql
import sshtunnel
from openpyxl import Workbook
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

ssh_host = '192.168.10.146'
ssh_username = 'sm-dev'
ssh_password = 'SM_dev@123'
database_username = 'vt2pniqibrqv6_ro'
database_password = 'FhMMJTrLejNYax3'
database_name = 'vt2pniqibrqv6'


def open_ssh_tunnel(verbose=False):
    """Open an SSH tunnel and connect using a username and password.

    :param verbose: Set to True to show logging
    :return tunnel: Global SSH tunnel connection
    """

    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG

    global tunnel
    tunnel = sshtunnel.SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=('127.0.0.1', 3306)  # Changed to the default MySQL port
    )

    tunnel.start()


def mysql_connect():
    """Connect to a MySQL server using the SSH tunnel connection

    :return connection: Global MySQL database connection
    """

    global connection

    connection = pymysql.connect(
        host='127.0.0.1',
        user=database_username,
        passwd=database_password,
        db=database_name,
        port=tunnel.local_bind_port
    )


def run_query(sql):
    """Runs a given SQL query via the global database connection.

    :param sql: MySQL query
    :return: Pandas dataframe containing results
    """

    return pd.read_sql_query(sql, connection)


def mysql_disconnect():
    """Closes the MySQL database connection.
    """

    connection.close()


def close_ssh_tunnel():
    """Closes the SSH tunnel connection.
    """

    tunnel.close()


def export_to_excel_and_drive(dataframe):
    """Exports the given Pandas DataFrame to an Excel file and uploads it to Google Drive.

    :param dataframe: Pandas DataFrame
    """

    # Tạo tên file dựa trên thời gian hiện tại
    current_time = datetime.datetime.now()
    file_name = f"data_{current_time.strftime('%d-%m-%Y')}.xlsx"
    excel_file_path = os.path.abspath(file_name)

    # Tạo file mới và thêm dữ liệu vào
    workbook = Workbook()
    sheet = workbook.active

    # Ghi tiêu đề cột
    headers = dataframe.columns
    sheet.append(headers)

    # Ghi dữ liệu từ DataFrame vào Excel
    for _, row in dataframe.iterrows():
        sheet.append(row.tolist())

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
    folder_id = 'your_folder_id'

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

    return uploaded_file_link


open_ssh_tunnel()
mysql_connect()
df = run_query("SELECT * FROM adjust_back LIMIT 5;")
df.head()
print(df.head())

# Xuất ra file Excel và upload lên Google Drive
uploaded_link = export_to_excel_and_drive(df)

# mysql_disconnect()
# close_ssh_tunnel()
