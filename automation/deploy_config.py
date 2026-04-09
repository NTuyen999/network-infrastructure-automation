import yaml
from automation.connect import connect_router


def load_routers(file_path="routers.yml"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "routers" not in data:
        return []

    return data["routers"]


def deploy_config():
    routers = load_routers()
    results = []

    if not routers:
        return [{"name": "-", "ip": "-", "status": "Thất bại", "detail": "Không có router nào trong routers.yml"}]

    for router in routers:
        try:
            conn = connect_router(router)

            commands = [
                "interface loopback0",
                f"ip address {router['loopback_ip']} 255.255.255.255",
                "no shutdown"
            ]

            output = conn.send_config_set(commands)
            conn.save_config()
            conn.disconnect()

            results.append({
                "name": router["name"],
                "ip": router["ip"],
                "status": "Thành công",
                "detail": output
            })

        except Exception as e:
            results.append({
                "name": router.get("name", "Unknown"),
                "ip": router.get("ip", "Unknown"),
                "status": "Thất bại",
                "detail": str(e)
            })

    return results