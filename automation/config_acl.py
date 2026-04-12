from automation.connect import connect_device


ERROR_KEYWORDS = [
    "% Invalid input",
    "% Incomplete command",
    "% Ambiguous command",
    "% Command rejected"
]


def has_config_error(output: str) -> bool:
    return any(err in output for err in ERROR_KEYWORDS)


def configure_block_guest_ping_dev(
    host,
    username,
    password,
    l3_interface,
    guest_subnet="192.168.30.0",
    guest_wildcard="0.0.0.255",
    dev_subnet="192.168.20.0",
    dev_wildcard="0.0.0.255",
    acl_name="BLOCK_GUEST_TO_DEV_PING",
    secret=None,
    device_type="cisco_ios"
):
    """
    Chặn VLAN 30 (Guest) ping sang VLAN 20 (Dev)
    bằng extended ACL gắn inbound trên interface L3 của VLAN 30.
    """

    required = [host, username, password, l3_interface]
    if any(not x for x in required):
        return {
            "success": False,
            "message": "Thiếu thông tin đầu vào"
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

        before_int = conn.send_command(
            f"show running-config interface {l3_interface}"
        )
        before_acl = conn.send_command(
            f"show running-config | section ip access-list extended {acl_name}"
        )

        commands = [
            f"no ip access-list extended {acl_name}",
            f"ip access-list extended {acl_name}",
            f"deny icmp {guest_subnet} {guest_wildcard} {dev_subnet} {dev_wildcard} echo",
            "permit ip any any",
            "exit",
            f"interface {l3_interface}",
            f"ip access-group {acl_name} in"
        ]

        config_output = conn.send_config_set(commands)

        if has_config_error(config_output):
            return {
                "success": False,
                "message": "Thiết bị báo lỗi khi cấu hình ACL",
                "before_interface": before_int,
                "before_acl": before_acl,
                "config_output": config_output
            }

        save_output = conn.save_config()

        verify_acl = conn.send_command(f"show access-lists {acl_name}")
        verify_int = conn.send_command(
            f"show running-config interface {l3_interface}"
        )

        return {
            "success": True,
            "message": f"Đã áp ACL {acl_name} chặn Guest ping Dev",
            "before_interface": before_int,
            "before_acl": before_acl,
            "config_output": config_output,
            "save_output": save_output,
            "verify_acl": verify_acl,
            "verify_interface": verify_int
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi khi cấu hình ACL: {str(e)}"
        }

    finally:
        if conn:
            conn.disconnect()