import re
from automation.connect import connect_device

# Đã bổ sung thêm "E" (e0/1 của GNS3) và "Po" (Port-channel) vào regex để nhận diện cổng
def validate_interface_name(interface):
    pattern = r"^(E|Eth|Ethernet|Fa|FastEthernet|Gi|GigabitEthernet|Te|TenGigabitEthernet|Po|Port-channel)\d+(?:/\d+)?(?:/\d+)?$"
    return re.match(pattern, interface, re.IGNORECASE) is not None

def configure_trunk_port(host, username, password, interface, allowed_vlans=None, native_vlan=None, secret=None):
    # 1. Kiểm tra đầu vào cơ bản
    if not host or not username or not password or not interface:
        return {
            "success": False,
            "message": "Thiếu thông tin đầu vào (IP, User, Pass, Interface)"
        }

    if not validate_interface_name(interface):
        return {
            "success": False,
            "message": f"Tên cổng không hợp lệ: {interface}. VD chuẩn: e0/1, gi0/1, Po1"
        }

    # 2. Kiểm tra Native VLAN (Phải là số từ 1 - 4094)
    if native_vlan not in [None, ""]:
        try:
            native_vlan = int(native_vlan)
            if native_vlan < 1 or native_vlan > 4094:
                return {"success": False, "message": "Native VLAN phải nằm trong khoảng 1 - 4094"}
        except ValueError:
            return {"success": False, "message": "Native VLAN phải là một con số"}
    else:
        native_vlan = None

    conn = None

    try:
        # 3. Kết nối vào thiết bị
        conn = connect_device(
            host=host,
            username=username,
            password=password,
            secret=secret
        )

        before_output = conn.send_command(f"show running-config interface {interface}")

        # 4. Soạn bộ lệnh cấu hình Trunking 
        commands = [
            f"interface {interface}",
            "switchport trunk encapsulation dot1q", 
            "switchport mode trunk"
        ]

        # Thêm luật Allowed VLANs (Nếu Web gửi xuống)
        if allowed_vlans and str(allowed_vlans).lower() != "all":
            # Dùng lệnh này để ghi đè (hoặc có thể dùng 'add' nếu muốn an toàn hơn)
            commands.append(f"switchport trunk allowed vlan {allowed_vlans}")
        
        # Thêm luật Native VLAN (Nếu Web gửi xuống)
        if native_vlan is not None:
            commands.append(f"switchport trunk native vlan {native_vlan}")

        # 5. Gửi lệnh xuống Switch
        config_output = conn.send_config_set(commands)

        # 6. Kiểm tra xem Switch có báo lỗi không
        error_keywords = [
            "% Invalid input",
            "% Incomplete command",
            "% Ambiguous command",
            "% Command rejected"
        ]

        for err in error_keywords:
            if err in config_output:
                return {
                    "success": False,
                    "message": "Thiết bị từ chối lệnh cấu hình Trunking",
                    "before_output": before_output,
                    "config_output": config_output
                }

        # 7. Lưu và kiểm tra lại
        save_output = conn.save_config()
        verify_output = conn.send_command(f"show running-config interface {interface}")

        return {
            "success": True,
            "message": f"Đã biến cổng {interface} thành Trunk Port thành công!",
            "before_output": before_output,
            "config_output": config_output,
            "save_output": save_output,
            "verify_output": verify_output
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Toang rớt mạng: {str(e)}"
        }

    finally:
        #  8. Đảm bảo ngắt kết nối sau khi xong việc
        if conn:
            conn.disconnect()