# Cliente para probar recv(buff_size) cuando buff_size < message_length.
# Para cada n envia un mensaje de 2n bytes; el servidor lo recibe con 2 llamadas a recv(n).
# Uso: python3 cliente_prueba_buffer.py [host] [puerto]
# (ejecutar despues de servidor_prueba_buffer.py, con el mismo puerto)
import sys
from sockettcp import SocketTCP

# n que no son multiplo de 16 (y 16 como caso de control). Debe coincidir con el servidor.
valores_n = [5, 7, 10, 13, 20, 25, 37, 16]

def mensaje_de_largo(largo):
    alfabeto = b"abcdefghijklmnopqrstuvwxyz0123456789"
    return bytes(alfabeto[i % len(alfabeto)] for i in range(largo))

host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
address = (host, port)

client_socketTCP = SocketTCP()
client_socketTCP.connect(address)
if not client_socketTCP.established:
    print(f"[Cliente] No se pudo establecer conexion con {address}")
    sys.exit(1)
print(f"[Cliente] Conectado a {address}")

for n in valores_n:
    message = mensaje_de_largo(2 * n)
    print(f"[Cliente] n={n}: enviando {len(message)} bytes: {message}")
    client_socketTCP.send(message)

client_socketTCP.close()
print("[Cliente] Conexion cerrada")
