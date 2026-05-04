from automation.connect import connect_device

def configure_ospf(host, username, password, secret, device_name, process_id="1", networks=None):
    if networks is None:
        networks = []
        
    conn = None
    try:
        conn = connect_device(host=host, username=username, password=password, secret=secret)
      
        ospf_commands = [f"router ospf {process_id}"]
       
        for net in networks:
            ospf_commands.append(net)
            
        config_output = conn.send_config_set(ospf_commands, cmd_verify=False)
        
        print(f"--- LOG OSPF CHO {host} ---")
        print(config_output)
        print("---------------------------")
        
        conn.save_config()

        return {
            "success": True,
            "message": f"{device_name} ({host}): Đã bơm OSPF thành công!"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"{device_name} ({host}): Lỗi cấu hình OSPF - {str(e)}"
        }
    finally:
        if conn:
            conn.disconnect()