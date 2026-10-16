# Cliente de prueba: envia un archivo (leido desde stdin) al servidor usando SocketTCP
# y luego cierra la conexion.
# Uso: python3 cliente_prueba.py localhost 8000 < archivo.txt
import sys
from sockettcp import SocketTCP

if len(sys.argv) != 3:
    print(f"Uso: python3 {sys.argv[0]} <host> <puerto> < archivo")
    sys.exit(1)

address = (sys.argv[1], int(sys.argv[2]))

# Se carga todo el archivo a memoria como arreglo de bytes
message = sys.stdin.buffer.read()

client_socketTCP = SocketTCP()
client_socketTCP.connect(address)
if not client_socketTCP.established:
    print(f"[Cliente] No se pudo establecer conexion con {address}")
    sys.exit(1)
print(f"[Cliente] Conectado a {address}")

print(f"[Cliente] Enviando {len(message)} bytes...")
client_socketTCP.send(message)
print("[Cliente] Envio terminado, cerrando conexion...")

client_socketTCP.close()
print("[Cliente] Conexion cerrada")
