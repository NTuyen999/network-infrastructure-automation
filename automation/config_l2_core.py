from automation.connect import connect_device
import re


ERROR_KEYWORDS = [
    "% Invalid input",
    "% Incomplete command",
    "% Ambiguous command",
    "% Command rejected",
    "%EC-",
    "% EtherChannel"
]


def normalize_interface_list(interfaces):
    """
    Hỗ trợ:
    - list: ["GigabitEthernet0/1", "GigabitEthernet0/2"]
    - string: "GigabitEthernet0/1, GigabitEthernet0/2"
    """
    if interfaces is None:
        return []

    if isinstance(interfaces, list):
        return [i.strip() for i in interfaces if str(i).strip()]

    if isinstance(interfaces, str):
        parts = re.split(r"[,\n;]+", interfaces)
        return [p.strip() for p in parts if p.strip()]

    return []


def validate_interface_name(interface):
    pattern = r"^(Eth|Ethernet|Fa|FastEthernet|Gi|GigabitEthernet|Te|TenGigabitEthernet|Po|Port-channel)\d+/\d+(?:/\d+)?$|^(Po|Port-channel)\d+$"
    return re.match(pattern, interface) is not None


def has_config_error(output):
    return any(err in output for err in ERROR_KEYWORDS)


def build_trunk_commands_for_interfaces(interfaces, allowed_vlans, native_vlan=None, description_prefix=None):
    commands = []

    for intf in interfaces:
        commands.append(f"interface {intf}")
        if description_prefix:
            commands.append(f"description {description_prefix} {intf}")
        commands.append("switchport")
        commands.append("switchport mode trunk")
        if native_vlan:
            commands.append(f"switchport trunk native vlan {native_vlan}")
        if allowed_vlans:
            commands.append(f"switchport trunk allowed vlan {allowed_vlans}")
        commands.append("no shutdown")

    return commands


def build_portchannel_commands(
    port_channel_id,
    member_interfaces,
    allowed_vlans,
    native_vlan=None,
    remote_name="REMOTE-CORE"
):
    commands = []

    # Cấu hình Port-channel logical interface
    commands.extend([
        f"interface Port-channel{port_channel_id}",
        f"description LACP to {remote_name}",
        "switchport",
        "switchport mode trunk"
    ])

    if native_vlan:
        commands.append(f"switchport trunk native vlan {native_vlan}")
    if allowed_vlans:
        commands.append(f"switchport trunk allowed vlan {allowed_vlans}")

    commands.append("no shutdown")

    # Cấu hình các member interface
    for intf in member_interfaces:
        commands.extend([
            f"interface {intf}",
            f"description LACP MEMBER to {remote_name} Po{port_channel_id}",
            "switchport",
            "switchport mode trunk"
        ])

        if native_vlan:
            commands.append(f"switchport trunk native vlan {native_vlan}")
        if allowed_vlans:
            commands.append(f"switchport trunk allowed vlan {allowed_vlans}")

        commands.extend([
            f"channel-group {port_channel_id} mode active",
            "no shutdown"
        ])

    return commands


def configure_single_core_l2(
    host,
    username,
    password,
    secret,
    switch_name,
    remote_name,
    port_channel_id,
    portchannel_members,
    allowed_vlans,
    native_vlan=None,
    extra_trunk_interfaces=None
):
    if not host or not username or not password:
        return {
            "success": False,
            "message": f"Thiếu thông tin đăng nhập của {switch_name}"
        }

    members = normalize_interface_list(portchannel_members)
    extra_trunks = normalize_interface_list(extra_trunk_interfaces)

    if not members:
        return {
            "success": False,
            "message": f"{switch_name}: Chưa có port thành viên EtherChannel"
        }

    for intf in members + extra_trunks:
        if not validate_interface_name(intf):
            return {
                "success": False,
                "message": f"{switch_name}: Interface không hợp lệ: {intf}"
            }

    conn = None

    try:
        conn = connect_device(
            host=host,
            username=username,
            password=password,
            secret=secret
        )

        before_po = conn.send_command(f"show running-config interface port-channel {port_channel_id}")
        before_ec = conn.send_command("show etherchannel summary")
        before_trunk = conn.send_command("show interfaces trunk")

        commands = []

        # 1. Cấu hình trunk thường cho các "đường chéo" hoặc link thường
        if extra_trunks:
            commands.extend(
                build_trunk_commands_for_interfaces(
                    interfaces=extra_trunks,
                    allowed_vlans=allowed_vlans,
                    native_vlan=native_vlan,
                    description_prefix=f"TRUNK-LINK-{switch_name}"
                )
            )

        # 2. Cấu hình EtherChannel LACP
        commands.extend(
            build_portchannel_commands(
                port_channel_id=port_channel_id,
                member_interfaces=members,
                allowed_vlans=allowed_vlans,
                native_vlan=native_vlan,
                remote_name=remote_name
            )
        )

        config_output = conn.send_config_set(commands)

        if has_config_error(config_output):
            return {
                "success": False,
                "message": f"{switch_name}: Lỗi khi đẩy cấu hình trunk/LACP",
                "config_output": config_output,
                "before_po": before_po,
                "before_ec": before_ec,
                "before_trunk": before_trunk
            }

        save_output = conn.save_config()

        verify_po = conn.send_command(f"show running-config interface port-channel {port_channel_id}")
        verify_ec = conn.send_command("show etherchannel summary")
        verify_trunk = conn.send_command("show interfaces trunk")

        return {
            "success": True,
            "message": f"{switch_name}: Cấu hình trunk + LACP thành công",
            "config_output": config_output,
            "save_output": save_output,
            "before_po": before_po,
            "before_ec": before_ec,
            "before_trunk": before_trunk,
            "verify_po": verify_po,
            "verify_ec": verify_ec,
            "verify_trunk": verify_trunk
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"{switch_name}: Lỗi kết nối hoặc cấu hình: {str(e)}"
        }

    finally:
        if conn:
            conn.disconnect()


def configure_l2_core_pair(
    core1,
    core2,
    port_channel_id,
    core1_po_members,
    core2_po_members,
    allowed_vlans,
    native_vlan=None,
    core1_extra_trunks=None,
    core2_extra_trunks=None
):
    """
    core1/core2 là dict:
    {
        "name": "CORE1",
        "host": "192.168.1.10",
        "username": "admin",
        "password": "cisco",
        "secret": "cisco"
    }
    """

    result_core1 = configure_single_core_l2(
        host=core1.get("host"),
        username=core1.get("username"),
        password=core1.get("password"),
        secret=core1.get("secret"),
        switch_name=core1.get("name", "CORE1"),
        remote_name=core2.get("name", "CORE2"),
        port_channel_id=port_channel_id,
        portchannel_members=core1_po_members,
        allowed_vlans=allowed_vlans,
        native_vlan=native_vlan,
        extra_trunk_interfaces=core1_extra_trunks
    )

    result_core2 = configure_single_core_l2(
        host=core2.get("host"),
        username=core2.get("username"),
        password=core2.get("password"),
        secret=core2.get("secret"),
        switch_name=core2.get("name", "CORE2"),
        remote_name=core1.get("name", "CORE1"),
        port_channel_id=port_channel_id,
        portchannel_members=core2_po_members,
        allowed_vlans=allowed_vlans,
        native_vlan=native_vlan,
        extra_trunk_interfaces=core2_extra_trunks
    )

    success = result_core1.get("success") and result_core2.get("success")

    return {
        "success": success,
        "message": "Hoàn tất cấu hình L2 Core Pair" if success else "Có lỗi trong quá trình cấu hình L2 Core Pair",
        "core1_result": result_core1,
        "core2_result": result_core2
    }