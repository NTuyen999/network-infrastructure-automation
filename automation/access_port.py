import re
from automation.connect import connect_device


def validate_interface_name(interface):
    pattern = r"^(Eth|Ethernet|Fa|FastEthernet|Gi|GigabitEthernet|Te|TenGigabitEthernet)\d+/\d+(?:/\d+)?$"
    return re.match(pattern, interface) is not None


def configure_access_port(host, username, password, interface, vlan=None, secret=None):
    if not host or not username or not password or not interface:
        return {
            "success": False,
            "message": "Thiếu thông tin đầu vào"
        }

    if not validate_interface_name(interface):
        return {
            "success": False,
            "message": f"Tên interface không hợp lệ: {interface}"
        }

    if vlan not in [None, ""]:
        try:
            vlan = int(vlan)
            if vlan < 1 or vlan > 4094:
                return {
                    "success": False,
                    "message": "VLAN phải nằm trong khoảng 1 - 4094"
                }
        except ValueError:
            return {
                "success": False,
                "message": "VLAN phải là số nguyên"
            }
    else:
        vlan = None

    conn = None

    try:
        conn = connect_device(
            host=host,
            username=username,
            password=password,
            secret=secret
        )

        before_output = conn.send_command(f"show running-config interface {interface}")

        commands = [
            f"interface {interface}",
            "switchport",
            "switchport mode access"
        ]

        if vlan is not None:
            commands.append(f"switchport access vlan {vlan}")

        config_output = conn.send_config_set(commands)

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
                    "message": "Thiết bị không hỗ trợ lệnh hoặc lệnh bị lỗi",
                    "before_output": before_output,
                    "config_output": config_output
                }

        save_output = conn.save_config()
        verify_output = conn.send_command(f"show running-config interface {interface}")

        return {
            "success": True,
            "message": f"Đã cấu hình {interface} thành access port thành công",
            "before_output": before_output,
            "config_output": config_output,
            "save_output": save_output,
            "verify_output": verify_output
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi khi cấu hình thiết bị: {str(e)}"
        }

    finally:
        if conn:
            conn.disconnect()