MySQL SSH to Google Drive Integration
Overview
This guide provides detailed steps for creating a Python script that connects to a MySQL server via SSH, performs a query, saves the results to a CSV file, and uploads that file to Google Drive. Additionally, the script sends a notification with the link to the file on Google Chat.

Requirements
Ensure you have the following prerequisites:

Python 3.x installed on your machine.
Steps
Step 1: Create a New Python File
Open your preferred code editor and create a new Python file. You can name it main.py or choose a name of your preference.

Step 2: Install Dependencies
Open your terminal or command prompt and run the following command to install the required Python libraries:

bash
Copy code
pip install paramiko mysql-connector-python tabulate pydrive
Step 3: Write the Script
Copy and paste the following Python script into your main.py file. This script establishes an SSH connection to a MySQL server, executes a query, saves the results to a CSV file, uploads the file to Google Drive, and sends a notification to Google Chat.

python
Copy code
# Import necessary libraries
import paramiko
import mysql.connector
import requests
import csv
from tabulate import tabulate
import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Define SSH and MySQL connection details
ssh_host = 'your_ssh_host'
ssh_port = 22
ssh_username = 'your_ssh_username'
ssh_password = 'your_ssh_password'

mysql_host = 'your_mysql_host'
mysql_user = 'your_mysql_username'
mysql_password = 'your_mysql_password'
mysql_db = 'your_mysql_database'

# Google Chat webhook
google_chat_webhook = 'your_google_chat_webhook_url'

try:
    # Establish SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)
    print("SSH connection successful!")

    # Create a TCP tunnel for MySQL over SSH
    ssh_channel = ssh.get_transport().open_channel('direct-tcpip', (mysql_host, 3306), ('127.0.0.1', 0))
    local_port = ssh_channel.getpeername()[1]

    # Connect to MySQL over SSH
    mysql_conn = mysql.connector.connect(
        host='127.0.0.1',
        port=local_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db
    )
    print("MySQL connection over SSH successful!")

    # Execute MySQL query
    select_query = "SELECT * FROM your_table"
    cursor = mysql_conn.cursor()
    cursor.execute(select_query)
    result = cursor.fetchall()

    # Check and send notification
    if not result:
        message = {"text": "No data found in the MySQL query result"}
        requests.post(google_chat_webhook, json=message)
    else:
        # Create CSV file
        headers = [i[0] for i in cursor.description]
        table = tabulate(result, headers, tablefmt="grid", disable_numparse=True)
        current_time = datetime.datetime.now()
        file_name = f'data_{current_time.strftime("%d-%m-%Y")}.csv'

        # Save data to CSV file
        csv_file_path = f'./{file_name}'
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(headers)
            csv_writer.writerows(result)

        # Authenticate with Google Drive
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)

        # Specify Google Drive folder ID
        folder_id = 'your_google_drive_folder_id'

        # Upload CSV file to Google Drive
        gdrive_file = drive.CreateFile({'title': file_name, 'parents': [{'id': folder_id}]})
        gdrive_file.SetContentFile(csv_file_path)
        gdrive_file.Upload()

        # Get the link to the uploaded file
        file_link = gdrive_file['alternateLink']
        print(f"File uploaded to Google Drive: {file_link}")

        # Send notification with file link
        message = {"text": f"Data from the table has been uploaded to Google Drive. [View file]({file_link})"}
        requests.post(google_chat_webhook, json=message)

except paramiko.AuthenticationException:
    print("Authentication error: Incorrect SSH username or password.")
except paramiko.SSHException as e:
    print(f"SSH connection error: {str(e)}")
except mysql.connector.Error as err:
    print(f"MySQL error: {err}")
except Exception as e:
    print(f"Unknown error: {str(e)}")

finally:
    # Close MySQL connection
    if 'mysql_conn' in locals():
        mysql_conn.close()

    # Close SSH connection
    if ssh.get_transport() is not None:
        ssh.get_transport().close()
Step 4: Configure the Script
Edit the script to include your SSH, MySQL, and Google Chat Webhook information.

Step 5: Run the Script
In the terminal, run the script using the following command:

bash
Copy code
python main.py
Step 6: Check the Results
The CSV file is saved locally with the format data_DD-MM-YYYY.csv.
The file is uploaded to Google Drive, and the link is notified on Google Chat.
Step 7: Additional Information
To create a Google Chat Webhook, you need administrator privileges in Google Workspace or have Chat API enabled.
To get the folder_id of the folder on Google Drive, check the URL of the folder. It will be in the format https://drive.google.com/drive/folders/{folder_id}.
This guide allows users to create a new Python script from scratch without the need to clone a repository. Adjust the script according to your specific use case and requirements.