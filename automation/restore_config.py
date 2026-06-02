from netmiko import ConnectHandler

def restore_device_config(device_info, filename):
    try:
        net_connect = ConnectHandler(**device_info)
        net_connect.enable()
        
        output = net_connect.send_config_from_file(filename, read_timeout=90)
        
        net_connect.save_config()
        net_connect.disconnect()
        return True, output
    except Exception as e:
        return False, str(e)