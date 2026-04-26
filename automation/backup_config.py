import os
from datetime import datetime
from automation.connect import connect_device

def backup_device_config(host, username, password, secret, device_name):
    conn = None
    try:
        # 1. Tạo thư mục backup nếu chưa có
        if not os.path.exists('backup'):
            os.makedirs('backup')

        # 2. Kết nối tới thiết bị
        conn = connect_device(host=host, username=username, password=password, secret=secret)
        
        # 3. Lấy cấu hình hiện tại
        config_data = conn.send_command("show running-config")
        
        # 4. Đặt tên file theo ngày giờ: R1_20260412_1830.txt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        file_name = f"backup/{device_name}_{timestamp}.txt"
        
        # 5. Ghi file vào ổ cứng laptop
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