from automation.connect import connect_device


ERROR_KEYWORDS = [
    "% Invalid input",
    "% Incomplete command",
    "% Ambiguous command",
    "% Command rejected"
]


def has_config_error(output: str) -> bool:
    return any(err in output for err in ERROR_KEYWORDS)


def configure_nat_overload(
    host,
    username,
    password,
    inside_interface,
    outside_interface,
    inside_subnet,
    wildcard_mask,
    acl_number=1,
    secret=None,
    device_type="cisco_ios"
):
    """
    Cấu hình NAT overload (PAT) cho LAN ra Internet trên Edge Router.

    Ví dụ:
    - inside_interface = "GigabitEthernet0/0"
    - outside_interface = "GigabitEthernet0/1"
    - inside_subnet = "192.168.10.0"
    - wildcard_mask = "0.0.0.255"
    - acl_number = 1
    """

    required_fields = [
        host, username, password,
        inside_interface, outside_interface,
        inside_subnet, wildcard_mask
    ]

    if any(not field for field in required_fields):
        return {
            "success": False,
            "message": "Thiếu thông tin đầu vào để cấu hình NAT"
        }

    conn = None

    try:
        conn = connect_device(
            host=host,
            username=username,
            password=password,
            secret=secret,
            device_type=device_type
        )

        # Lấy cấu hình trước khi thay đổi
        before_inside = conn.send_command(
            f"show running-config interface {inside_interface}"
        )
        before_outside = conn.send_command(
            f"show running-config interface {outside_interface}"
        )
        before_nat = conn.send_command("show running-config | include ip nat")
        before_acl = conn.send_command(f"show access-lists {acl_number}")

        commands = [
            f"access-list {acl_number} permit {inside_subnet} {wildcard_mask}",
            f"interface {inside_interface}",
            "ip nat inside",
            "exit",
            f"interface {outside_interface}",
            "ip nat outside",
            "exit",
            f"ip nat inside source list {acl_number} interface {outside_interface} overload"
        ]

        config_output = conn.send_config_set(commands)

        if has_config_error(config_output):
            return {
                "success": False,
                "message": "Thiết bị báo lỗi khi cấu hình NAT",
                "before_inside": before_inside,
                "before_outside": before_outside,
                "before_nat": before_nat,
                "before_acl": before_acl,
                "config_output": config_output
            }

        save_output = conn.save_config()

        verify_inside = conn.send_command(
            f"show running-config interface {inside_interface}"
        )
        verify_outside = conn.send_command(
            f"show running-config interface {outside_interface}"
        )
        verify_nat = conn.send_command("show running-config | include ip nat")
        verify_acl = conn.send_command(f"show access-lists {acl_number}")

        return {
            "success": True,
            "message": f"Đã cấu hình NAT overload thành công trên {host}",
            "before_inside": before_inside,
            "before_outside": before_outside,
            "before_nat": before_nat,
            "before_acl": before_acl,
            "config_output": config_output,
            "save_output": save_output,
            "verify_inside": verify_inside,
            "verify_outside": verify_outside,
            "verify_nat": verify_nat,
            "verify_acl": verify_acl
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi khi cấu hình NAT: {str(e)}"
        }

    finally:
        if conn:
            conn.disconnect()