# Servidor de prueba: recibe un archivo enviado por cliente_prueba.py usando SocketTCP,
# lo imprime en salida estandar y luego maneja el cierre de conexion.
# Uso: python3 servidor_prueba.py [puerto] [buff_size]
#   - Sin buff_size se usa un buffer grande, por lo que un solo recv trae todo el mensaje.
#   - Con buff_size se llama a recv(buff_size) las veces necesarias hasta completar el
#     mensaje (sirve para probar el caso buff_size < message_length).
import sys
from sockettcp import SocketTCP

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
buff_size = int(sys.argv[2]) if len(sys.argv) > 2 else 2**20
address = ("localhost", port)

server_socketTCP = SocketTCP()
server_socketTCP.bind(address)
print(f"[Servidor] Escuchando en {address}...")
connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[Servidor] Conexion aceptada desde {new_address}")

full_message = b""
llamada = 1
while True:
    part = connection_socketTCP.recv(buff_size)
    print(f"[Servidor] recv({buff_size}) #{llamada} -> {len(part)} bytes: {part}")
    if len(part) > buff_size:
        print(f"[Servidor] ERROR: recv retorno mas de buff_size={buff_size} bytes")
    full_message += part
    llamada += 1
    # SocketTCP reinicia received_bytes a 0 cuando ya entrego el mensaje completo
    if connection_socketTCP.received_bytes == 0:
        break

print(f"[Servidor] Mensaje completo ({len(full_message)} bytes):")
sys.stdout.buffer.write(full_message)
sys.stdout.buffer.write(b"\n")
sys.stdout.flush()

connection_socketTCP.recv_close()
print("[Servidor] Conexion cerrada")
