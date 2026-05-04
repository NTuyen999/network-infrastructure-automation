from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import paramiko

def connect_device(host, username, password, secret=None, device_type="cisco_ios"):
    device = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "conn_timeout": 15,
        "auth_timeout": 15,
    }

    if secret:
        device["secret"] = secret
    try:
        connection = ConnectHandler(**device)
        if secret:
            connection.enable()
            
        return connection

    except NetmikoAuthenticationException:
        raise Exception(f"❌ Lỗi xác thực: Sai Username hoặc Password trên thiết bị {host}!")
        
    except NetmikoTimeoutException:
        raise Exception(f"❌ Rớt mạng: Không thể kết nối tới {host}. Quá thời gian chờ (Timeout) hoặc cấu hình sai IP!")
        
    except paramiko.ssh_exception.SSHException as e:
        raise Exception(f"❌ Lỗi SSH/Socket: Thiết bị {host} từ chối kết nối (Có thể do kẹt cổng VTY chưa giải phóng). Chi tiết: {str(e)}")
        
    except Exception as e:
        raise Exception(f"❌ Lỗi không xác định khi kết nối {host}: {str(e)}")

def connect_router(router):
    return connect_device(
        host=router["ip"],
        username=router["username"],
        password=router["password"],
        secret=router.get("secret", ""),
        device_type=router["device_type"]
    )