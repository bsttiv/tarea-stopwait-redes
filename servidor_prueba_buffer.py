# Servidor para probar recv(buff_size) cuando buff_size < message_length.
# Para cada n recibe un mensaje de 2n bytes llamando 2 veces a recv(n).
# Uso: python3 servidor_prueba_buffer.py [puerto]
# (ejecutar antes que cliente_prueba_buffer.py, con el mismo puerto)
import sys
from sockettcp import SocketTCP

# n que no son multiplo de 16 (y 16 como caso de control). Debe coincidir con el cliente.
valores_n = [5, 7, 10, 13, 20, 25, 37, 16]

def mensaje_de_largo(largo):
    alfabeto = b"abcdefghijklmnopqrstuvwxyz0123456789"
    return bytes(alfabeto[i % len(alfabeto)] for i in range(largo))

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
address = ("localhost", port)

server_socketTCP = SocketTCP()
server_socketTCP.bind(address)
print(f"[Servidor] Escuchando en {address}...")
connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[Servidor] Conexion aceptada desde {new_address}")

resultados = []
for n in valores_n:
    esperado = mensaje_de_largo(2 * n)
    part_1 = connection_socketTCP.recv(n)
    part_2 = connection_socketTCP.recv(n)
    ok = (part_1 + part_2 == esperado and len(part_1) == n and len(part_2) == n)
    resultados.append((n, ok))
    print(f"[Servidor] n={n}: recv#1={part_1} recv#2={part_2} -> {'Passed' if ok else 'Failed'}")

connection_socketTCP.recv_close()
print("[Servidor] Conexion cerrada")

print("\n===== Resumen =====")
for n, ok in resultados:
    print(f"n={n:3d} (mensaje de {2*n} bytes, multiplo de 16: {n % 16 == 0}): {'Passed' if ok else 'Failed'}")
print("Todas pasaron" if all(ok for _, ok in resultados) else "Hubo fallas")
