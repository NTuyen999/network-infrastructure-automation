from netmiko import ConnectHandler


def connect_router(router):
    connection = ConnectHandler(
        device_type=router["device_type"],
        host=router["ip"],
        username=router["username"],
        password=router["password"],
    )
    return connection