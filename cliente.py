import sockettcp

address = ("127.0.0.1", 5000)

# CLIENT
client_socketTCP = sockettcp.SocketTCP()
client_socketTCP.connect(address)
print(f"[Cliente] Conectado a {address}")

# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message)

# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

client_socketTCP.close()