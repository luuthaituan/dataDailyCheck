import paramiko
import mysql.connector

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

    # Nhập dữ liệu từ bàn phím
    name = input("Nhập tên: ")
    address = input("Nhập địa chỉ: ")

    # Thực hiện truy vấn SQL để thêm dữ liệu
    insert_query = "INSERT INTO test (name, address) VALUES (%s, %s)"
    insert_data = (name, address)

    cursor = mysql_conn.cursor()
    cursor.execute(insert_query, insert_data)
    mysql_conn.commit()

    print("Dữ liệu đã được thêm vào bảng!")

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
