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
from oauth2client.service_account import ServiceAccountCredentials


def open_ssh_tunnel(config, verbose=False):
    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG

    tunnel = sshtunnel.SSHTunnelForwarder(
        ssh_address=(config["ssh"]["host"], config["ssh"]["port"]),
        ssh_username=config["ssh"]["username"],
        ssh_password=config["ssh"]["password"],
        remote_bind_address=('127.0.0.1', 3306)
    )

    tunnel.start()
    return tunnel


def mysql_connect(config, tunnel):
    connection = pymysql.connect(
        host='127.0.0.1',
        user=config["mysql"]["user"],
        passwd=config["mysql"]["password"],
        db=config["mysql"]["db"],
        port=tunnel.local_bind_port
    )
    return connection


def run_query(sql, connection):
    return pd.read_sql_query(sql, connection)


def mysql_disconnect(connection):
    connection.close()


def close_ssh_tunnel(tunnel):
    tunnel.close()


def send_message_to_google_chat(link, config):
    message = {
        "text": f"Order 5.0 - Dữ liệu trong bảng đã được upload lên Google Drive. [Xem file]({link})"
    }
    requests.post(config["google_chat_webhook"], json=message)


def read_credentials_from_file(credentials_file_path):
    with open(credentials_file_path, 'r') as credentials_file:
        credentials = json.load(credentials_file)
    return credentials


def export_to_excel_and_drive(dataframe, config):
    if dataframe.empty:
        # Gửi thông báo không có dữ liệu
        message = {"text": "Không có dữ liệu"}
        requests.post(config["google_chat_webhook"], json=message)
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

    credentials_path = "credentials.json"  # Thay đổi đường dẫn nếu cần
    credentials = read_credentials_from_file(credentials_path)

    gauth = GoogleAuth()
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials,
                                                                         ['https://www.googleapis.com/auth/drive'])

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
    send_message_to_google_chat(uploaded_file_link, config)


if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    tunnel = open_ssh_tunnel(config)
    connection = mysql_connect(config, tunnel)

    try:
        df = run_query("SELECT * FROM local.test;", connection)
        df.head()
        print(df.head())

        export_to_excel_and_drive(df, config)

    finally:
        mysql_disconnect(connection)
        close_ssh_tunnel(tunnel)
