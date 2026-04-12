from netmiko import ConnectHandler


def connect_router(router):
    connection = ConnectHandler(
        device_type=router["device_type"],
        host=router["ip"],
        username=router["username"],
        password=router["password"],
        secret=router.get("secret", "")
    )

    if router.get("secret"):
        connection.enable()

    return connection


def connect_device(host, username, password, secret=None, device_type="cisco_ios"):
    device = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
    }

    if secret:
        device["secret"] = secret

    connection = ConnectHandler(**device)

    if secret:
        connection.enable()

    return connection