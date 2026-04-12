from flask import Blueprint, request, jsonify
from automation.access_port import configure_access_port
from automation.config_l2_core import configure_l2_core_pair
from automation.config_security import configure_nat_overload
from automation.config_acl import configure_block_guest_ping_dev

api_bp = Blueprint("api_bp", __name__)

@api_bp.route("/access-port", methods=["POST"])
def access_port():
    data = request.get_json()

    result = configure_access_port(
        host=data.get("host"),
        username=data.get("username"),
        password=data.get("password"),
        interface=data.get("interface"),
        vlan=data.get("vlan"),
        secret=data.get("secret")
    )

    return jsonify(result), 200 if result["success"] else 400


@api_bp.route("/l2-core", methods=["POST"])
def config_l2_core():
    data = request.get_json()

    core1 = {
        "name": data.get("core1_name"),
        "host": data.get("core1_host"),
        "username": data.get("core1_username"),
        "password": data.get("core1_password"),
        "secret": data.get("core1_secret")
    }

    core2 = {
        "name": data.get("core2_name"),
        "host": data.get("core2_host"),
        "username": data.get("core2_username"),
        "password": data.get("core2_password"),
        "secret": data.get("core2_secret")
    }

    result = configure_l2_core_pair(
        core1=core1,
        core2=core2,
        port_channel_id=data.get("port_channel_id"),
        core1_po_members=data.get("core1_po_members"),
        core2_po_members=data.get("core2_po_members"),
        allowed_vlans=data.get("allowed_vlans"),
        native_vlan=data.get("native_vlan"),
        core1_extra_trunks=data.get("core1_extra_trunks"),
        core2_extra_trunks=data.get("core2_extra_trunks")
    )

    return jsonify(result), 200 if result["success"] else 400


@api_bp.route("/config-security/nat", methods=["POST"])
def config_security_nat():
    data = request.get_json(silent=True) or {}

    result = configure_nat_overload(
        host=data.get("host"),
        username=data.get("username"),
        password=data.get("password"),
        inside_interface=data.get("inside_interface"),
        outside_interface=data.get("outside_interface"),
        inside_subnet=data.get("inside_subnet"),
        wildcard_mask=data.get("wildcard_mask"),
        acl_number=data.get("acl_number", 1),
        secret=data.get("secret"),
        device_type=data.get("device_type", "cisco_ios")
    )

    return jsonify(result), 200 if result["success"] else 400

@api_bp.route("/acl/block-guest-ping-dev", methods=["POST"])
def block_guest_ping_dev():
    data = request.get_json(silent=True) or {}

    result = configure_block_guest_ping_dev(
        host=data.get("host"),
        username=data.get("username"),
        password=data.get("password"),
        secret=data.get("secret"),
        device_type=data.get("device_type", "cisco_ios"),
        l3_interface=data.get("l3_interface"),
        guest_subnet=data.get("guest_subnet", "192.168.30.0"),
        guest_wildcard=data.get("guest_wildcard", "0.0.0.255"),
        dev_subnet=data.get("dev_subnet", "192.168.20.0"),
        dev_wildcard=data.get("dev_wildcard", "0.0.0.255"),
        acl_name=data.get("acl_name", "BLOCK_GUEST_TO_DEV_PING")
    )

    return jsonify(result), 200 if result["success"] else 400