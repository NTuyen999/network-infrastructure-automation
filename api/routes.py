from flask import Blueprint, request, jsonify
from automation.trunking import configure_trunk_port
from automation.config_security import configure_nat_overload
from automation.config_acl import dynamic_acl_ping, block_subnet_ping

api_bp = Blueprint("api_bp", __name__)

@api_bp.route("/trunking", methods=["POST"])  # Đổi route thành /trunking cho khớp với HTML
def api_trunking():
    data = request.get_json()
    result = configure_trunk_port(
        host=data.get("host"),
        username=data.get("username"),
        password=data.get("password"),
        secret=data.get("secret", "cisco"), 
        interface=data.get("interface"),
        allowed_vlans=data.get("allowed_vlans", "all"),
        native_vlan=data.get("native_vlan", "1")
    )

    return jsonify(result), 200 if result["success"] else 400

# Đừng quên import hàm NAT vào ở phía trên file nha:
from automation.config_security import configure_nat_overload 

@api_bp.route("/nat", methods=["POST"])
def config_security_nat():
    data = request.get_json(silent=True) or {}
    result = configure_nat_overload(
        host=data.get("host"),  # Đã xóa IP ảo 192.168.99.1, bắt buộc lấy từ Web
        username=data.get("username", "admin"),
        password=data.get("password", "cisco"),
        secret=data.get("secret", "cisco"),
        inside_interface=data.get("inside_interface"),
        outside_interface=data.get("outside_interface"),
        inside_subnet=data.get("inside_subnet", "192.168.0.0"),
        wildcard_mask=data.get("wildcard_mask", "0.0.255.255"),
        acl_number=data.get("acl_number", 1),
        device_type=data.get("device_type", "cisco_ios")
    )
    return jsonify(result), 200 if result.get("success") else 400

# Route cho nút "Áp ACL" (Chặn nguyên 1 mạng)
@api_bp.route("/acl/block-guest-ping-dev", methods=["POST"])
def block_guest_ping_dev():
    data = request.get_json(silent=True) or {}

    # Gọi hàm block_subnet_ping thay vì dynamic
    result = block_subnet_ping(
        host=data.get("host"),
        username=data.get("username"),
        password=data.get("password"),
        secret=data.get("secret", "cisco"),
        interface_name=data.get("l3_interface"), # Web gửi lên l3_interface, Python nhận interface_name
        source_subnet=data.get("guest_subnet", "192.168.30.0"),
        source_wildcard=data.get("guest_wildcard", "0.0.0.255"),
        dest_subnet=data.get("dev_subnet", "192.168.20.0"),
        dest_wildcard=data.get("dev_wildcard", "0.0.0.255"),
        acl_name=data.get("acl_name", "BLOCK_GUEST")
    )

    return jsonify(result), 200 if result["success"] else 400

from automation.backup_config import backup_device_config

@api_bp.route("/backup", methods=["POST"])
def backup_config():
    data = request.get_json()
    
    # Gọi hàm backup mà anh em mình đã viết ở file automation/backup_config.py
    result = backup_device_config(
        host=data.get("host"), # Lấy IP từ Web gửi lên
        username=data.get("username"),
        password=data.get("password"),
        secret=data.get("secret"),
        device_name=data.get("device_name")
    )
    
    return jsonify(result), 200 if result["success"] else 400

from automation.config_ospf import configure_ospf

@api_bp.route("/ospf", methods=["POST"])
def api_ospf_route():
    data = request.get_json()
    result = configure_ospf(
        host=data.get("host"),
        username=data.get("username", "admin"),
        password=data.get("password", "cisco"),
        secret=data.get("secret", "cisco"),
        device_name=data.get("host"), 
        process_id=data.get("process_id", "1"),
        networks=data.get("networks", [])
    )
    
    return jsonify(result), 200 if result["success"] else 400