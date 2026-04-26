from automation.connect import connect_device

def configure_ospf(host, username, password, secret, device_name, is_router=False):
    conn = None
    try:
        conn = connect_device(host=host, username=username, password=password, secret=secret)
        
        if is_router:
            ospf_commands = [
                "router ospf 1",
                "network 192.168.99.0 0.0.0.255 area 0",
                "default-information originate"
            ]
        else: # Dành cho Switch Core
            ospf_commands = [
                "router ospf 1",
                "network 192.168.99.0 0.0.0.255 area 0",
                "network 192.168.10.0 0.0.0.255 area 0",
                "network 192.168.20.0 0.0.0.255 area 0",
                "network 192.168.30.0 0.0.0.255 area 0"
            ]

        config_output = conn.send_config_set(ospf_commands, cmd_verify=False)
        conn.save_config()

        return {
            "success": True,
            "message": f"{device_name}: Đã bơm OSPF thành công!"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"{device_name}: Lỗi cấu hình OSPF - {str(e)}"
        }
    finally:
        if conn:
            conn.disconnect()