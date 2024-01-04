import datetime
import logging
import os
import pandas as pd
import pymysql
import sshtunnel
from openpyxl import Workbook
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import requests
import json


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

ssh_host = config["ssh"]["host"]
ssh_username = config["ssh"]["username"]
ssh_password = config["ssh"]["password"]
database_username = config["mysql"]["user"]
database_password = config["mysql"]["password"]
database_name = config["mysql"]["db"]
google_chat_webhook = config["google_chat_webhook"]


def open_ssh_tunnel(verbose=False):
    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG

    global tunnel
    tunnel = sshtunnel.SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=('127.0.0.1', 3306)
    )

    tunnel.start()


def mysql_connect():
    global connection
    connection = pymysql.connect(
        host='127.0.0.1',
        user=database_username,
        passwd=database_password,
        db=database_name,
        port=tunnel.local_bind_port
    )


def run_query(sql):
    return pd.read_sql_query(sql, connection)


def mysql_disconnect():
    connection.close()


def close_ssh_tunnel():
    tunnel.close()


def send_message_to_google_chat(link, monitoring_name='Order 5.0', webhook_url=google_chat_webhook):
    message = {
        "text": f"{monitoring_name} - Dữ liệu trong bảng đã được upload lên Google Drive. [Xem file]({link})"
    }
    requests.post(webhook_url, json=message)


def export_to_excel_and_drive(dataframe):
    if dataframe.empty:
        # Gửi thông báo không có dữ liệu
        message = {"text": "Không có dữ liệu"}
        requests.post(google_chat_webhook, json=message)
        return  # Kết thúc hàm nếu không có dữ liệu

    current_time = datetime.datetime.now()
    file_name = f"data_{current_time.strftime('%d-%m-%Y')}.xlsx"
    excel_file_path = os.path.abspath(file_name)

    workbook = Workbook()
    sheet = workbook.active

    # Convert headers to a list
    headers = list(dataframe.columns)
    sheet.append(headers)

    for _, row in dataframe.iterrows():
        sheet.append(row.tolist())

    workbook.save(excel_file_path)

    gauth = GoogleAuth()
    creds_file_path = os.path.abspath("mycreds.txt")

    if not os.path.exists(creds_file_path):
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile(creds_file_path)

    gauth.LoadCredentialsFile(creds_file_path)

    folder_id = config["drive_folder_id"]
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': f"title='{file_name}' and '{folder_id}' in parents and trashed=false"}).GetList()

    if file_list:
        existing_file = file_list[0]
        existing_file.Delete()

    gdrive_file = drive.CreateFile({'title': file_name, 'parents': [{'id': folder_id}]})
    gdrive_file.SetContentFile(excel_file_path)
    gdrive_file.Upload()

    uploaded_file_link = gdrive_file['alternateLink']
    print(f"File uploaded to Google Drive: {uploaded_file_link}")

    # Gửi link Google Drive qua Google Chat
    send_message_to_google_chat(uploaded_file_link)


open_ssh_tunnel()
mysql_connect()
df = run_query("SELECT * FROM local.test;")
df.head()
print(df.head())

# Xuất ra file Excel và upload lên Google Drive
export_to_excel_and_drive(df)

# Đóng kết nối
mysql_disconnect()
close_ssh_tunnel()
