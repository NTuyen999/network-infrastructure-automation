from netmiko import ConnectHandler

#Hàm chặn cả mạng
def block_subnet_ping(host, username, password, interface_name, source_subnet, source_wildcard, dest_subnet, dest_wildcard, acl_name, secret="cisco"):
    cisco_device = {
        'device_type': 'cisco_ios', 'host': host, 'username': username,
        'password': password, 'secret': secret
    }
    conn = None
    try:
        conn = ConnectHandler(**cisco_device)
        conn.enable()
        
        # Lệnh Cisco dùng cho Subnet
        commands = [
            f"ip access-list extended {acl_name}",
            f"deny icmp {source_subnet} {source_wildcard} {dest_subnet} {dest_wildcard} echo",
            "permit ip any any",
            "exit",
            f"interface {interface_name}",
            f"ip access-group {acl_name} in"
        ]
        
        output = conn.send_config_set(commands)
        conn.save_config()
        
        return {"success": True, "message": f"Đã áp ACL {acl_name} chặn mạng {source_subnet} thành công!"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi cấu hình: {str(e)}"}
    finally:
        if conn: conn.disconnect()



#Hàm chặn 1 Host cụ thể
def dynamic_acl_ping(host, username, password, interface_name, source_ip, dest_ip, secret="cisco"):
    cisco_device = {
        'device_type': 'cisco_ios', 'host': host, 'username': username,
        'password': password, 'secret': secret
    }
    conn = None
    try:
        conn = ConnectHandler(**cisco_device)
        conn.enable()
        
        # Lệnh Cisco dùng cho Host (1 máy)
        commands = [
            "ip access-list extended DYNAMIC_BLOCK",
            # BƯỚC 1: Xóa cái thẻ bài miễn tử hiện tại đi (Nếu chưa có thì nó báo lỗi xíu không sao)
            "no permit ip any any", 
            
            # BƯỚC 2: Thêm luật cấm mới vào (Nó sẽ tự lấy số thứ tự tiếp theo)
            f"deny icmp host {source_ip} host {dest_ip} echo",
            
            # BƯỚC 3: Chốt sổ lại bằng thẻ bài miễn tử ở dưới cùng
            "permit ip any any",
            
            "exit",
            f"interface {interface_name}",
            "ip access-group DYNAMIC_BLOCK in"
        ]
        
        output = conn.send_config_set(commands)
        conn.save_config()
        
        return {"success": True, "message": f"Đã khóa mõm! Máy {source_ip} không thể ping {dest_ip}."}
    except Exception as e:
        return {"success": False, "message": f"Lỗi cấu hình: {str(e)}"}
    finally:
        if conn: conn.disconnect()