from flask import Flask, render_template, request, redirect, url_for, jsonify
import yaml
import os
import datetime

from automation.deploy_config import deploy_config
from api.routes import api_bp
from automation.connect import connect_device 
from automation.config_acl import dynamic_acl_ping

app = Flask(__name__)

ROUTERS_FILE = "routers.yml"

def load_routers():
    if not os.path.exists(ROUTERS_FILE):
        return {"routers": []}
    with open(ROUTERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "routers" not in data:
        return {"routers": []}
    return data

def save_routers(data):
    with open(ROUTERS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

# Đăng ký blueprint API
app.register_blueprint(api_bp, url_prefix="/api")

@app.route("/")
def index():
    data = load_routers()
    return render_template("index.html", routers=data["routers"])

@app.route("/add_router", methods=["POST"])
def add_router():
    data = load_routers()
    new_router = {
        "name": request.form["name"].strip(),
        "ip": request.form["ip"].strip(),
        "device_type": request.form["device_type"].strip(),
        "username": request.form["username"].strip(),
        "password": request.form["password"].strip(),
        "loopback_ip": request.form["loopback_ip"].strip()
    }
    data["routers"].append(new_router)
    save_routers(data)
    return redirect(url_for("index"))

@app.route("/deploy")
def deploy():
    results = deploy_config()
    return render_template("result.html", results=results)


# 1. Cấu hình OSPF
@app.route('/api/ospf', methods=['POST'])
def api_ospf():
    data = request.json
    try:
        conn = connect_device(data['host'], data['username'], data['password'], data['secret'])
        cmds = [f"router ospf {data['process_id']}"]
        for net in data['networks']:
            cmds.append(f"network {net} area {data['area']}")
        conn.send_config_set(cmds, delay_factor=2)
        conn.save_config()
        conn.disconnect()
        return jsonify({"success": True, "message": "Đã cấu hình OSPF thành công!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi Python: {str(e)}"})


# Cấu hình Trunking Port (802.1Q)
@app.route('/api/trunking', methods=['POST'])
def api_trunking():
    data = request.json
    try:
        # 1. Kết nối vào thiết bị
        conn = connect_device(
            data['host'], 
            data['username'], 
            data['password'], 
            data.get('secret', 'cisco')
        )
        
        # 2. Lấy dữ liệu từ Web gửi xuống
        interface = data['interface']
        allowed_vlans = data.get('allowed_vlans', 'all')
        native_vlan = data.get('native_vlan', '1')

        # 3. Lên danh sách lệnh Trunking chuẩn bài
        cmds = [
            f"interface {interface}",
            "switchport", # Ép cổng thành Layer 2 (Rất cần cho Switch L3)
            "switchport trunk encapsulation dot1q", # Bùa hộ mệnh: Lệnh bắt buộc trên Switch L3 ảo GNS3
            "switchport mode trunk"
        ]

        # 4. Xử lý phần Allowed VLANs (Danh sách khách VIP)
        if allowed_vlans and str(allowed_vlans).lower() != "all":
            cmds.append(f"switchport trunk allowed vlan {allowed_vlans}")

        # 5. Xử lý phần Native VLAN (Phòng chờ Untagged)
        if native_vlan and str(native_vlan) != "1":
            cmds.append(f"switchport trunk native vlan {native_vlan}")

        cmds.append("no shutdown")

        # 6. Đẩy lệnh, lưu và thoát
        conn.send_config_set(cmds)
        conn.save_config()
        conn.disconnect()
        
        return jsonify({"success": True, "message": f"Đã thông ống Trunking trên cổng {interface} thành công!"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Toang cấu hình Trunking: {str(e)}"})


# 4. Cấu hình NAT
@app.route('/config-security/nat', methods=['POST'])
def api_nat():
    data = request.json
    try:
        conn = connect_device(data['host'], data['username'], data['password'], data['secret'])
        cmds = [
            f"access-list {data['acl_number']} permit {data['inside_subnet']} {data['wildcard_mask']}",
            f"ip nat inside source list {data['acl_number']} interface {data['outside_interface']} overload",
            f"interface {data['inside_interface']}",
            "ip nat inside",
            f"interface {data['outside_interface']}",
            "ip nat outside"
        ]
        conn.send_config_set(cmds)
        conn.save_config()
        conn.disconnect()
        return jsonify({"success": True, "message": "Cấu hình NAT thành công! Mạng đã thông."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 5. Áp dụng ACL
@app.route('/api/custom-acl', methods=['POST'])
def tao_acl_tuy_chon():
    data = request.json
    
    # Lấy IP do người dùng gõ trên Web
    ip_nguon = data.get('source_ip') 
    ip_dich = data.get('dest_ip')
    
    # Lôi cái hàm ở trên ra chạy
    ket_qua = dynamic_acl_ping(
        host="192.168.99.11", 
        username="admin", 
        password="cisco", 
        interface_name="Vlan30",
        source_ip=ip_nguon, 
        dest_ip=ip_dich
    )
    
    return jsonify(ket_qua)

# 6. Sao lưu cấu hình
@app.route('/api/backup', methods=['POST'])
def api_backup():
    data = request.json
    try:
        conn = connect_device(data['host'], data['username'], data['password'], data['secret'])
        output = conn.send_command("show running-config")
        conn.disconnect()
        if not os.path.exists('backup'):
            os.makedirs('backup')
        filename = f"backup/{data['device_name']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(output)
        return jsonify({"success": True, "message": f"✅ Đã hút cấu hình về file: {filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)