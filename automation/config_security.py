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

        # 1. Gom tất cả lệnh cấu hình lại
        commands = [
            f"no access-list {acl_number}",
            "no ip nat inside source list 1 interface", 
            f"access-list {acl_number} permit {inside_subnet} {wildcard_mask}",
            f"interface {inside_interface}",
            "ip nat inside",
            "exit",
            f"interface {outside_interface}",
            "ip nat outside",
            "exit",
            f"ip nat inside source list {acl_number} interface {outside_interface} overload"
        ]

        # 2. Bắn lệnh với bùa hộ mệnh: read_timeout=120 
        # Ép Python phải ngồi đợi tối đa 120 giây cho Router ảo xử lý xong
        config_output = conn.send_config_set(commands, read_timeout=120)

        # 3. Lưu cấu hình (cũng cho thêm timeout cho chắc ăn)
        save_output = conn.save_config(read_timeout=120)

        # Trả về kết quả luôn, dẹp mấy lệnh show rườm rà đi cho nhẹ API
        return {
            "success": True,
            "message": f"Đã cấu hình NAT Overload thành công rực rỡ trên {host}",
            "config_output": config_output
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi NAT do mạng hoặc thiết bị ảo lag: {str(e)}"
        }


    finally:
        if conn:
            conn.disconnect()