import os
from datetime import datetime
from automation.connect import connect_device

def backup_device_config(host, username, password, secret, device_name):
    conn = None
    try:
        if not os.path.exists('backup'):
            os.makedirs('backup')
        conn = connect_device(host=host, username=username, password=password, secret=secret)
        config_data = conn.send_command("show running-config")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        file_name = f"backup/{device_name}_{timestamp}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(config_data)
        
        return {
            "success": True, 
            "message": f"Đã lưu cấu hình {device_name} vào file {file_name} thành công!"
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi backup {device_name}: {str(e)}"}
    finally:
        if conn:
            conn.disconnect()