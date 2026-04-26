from netmiko import ConnectHandler

r1_device = {
    "device_type": "cisco_ios",
    'host' : '192.168.153.129',
    'username' : 'admin',
    'password' : 'cisco',
    'secret' : 'cisco',
}
conection = ConnectHandler(**r1_device)
conection.enable()
output = conection.send_command("show ip int brief")
print(output)