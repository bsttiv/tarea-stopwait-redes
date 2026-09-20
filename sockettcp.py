import socket
import random
import time

SYN = 1
ACK = 2
FIN = 4

DEBUG = True

class TCPSegment:
    def __init__(self, flags, seq, data):
        self.syn = bool(flags & SYN)
        self.ack = bool(flags & ACK)
        self.fin = bool(flags & FIN)
        self.flags = flags
        self.seq = seq
        self.data = data

class SocketTCP:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dest = ("", 0)
        self.established = False
        self.num = 0
        self.received_bytes = 0
        self.remaining_msg = b""
        self.last_message_length = 0

    @staticmethod
    def parse_segment(segment):
        # Los headers del segmento TCP son los primero 4 bytes
        headers = int.from_bytes(segment[:4], byteorder='big')
        # Los primeros 3 bits indican si es un SYN, ACK, FIN o alguna combinación
        # los otros 29 corresponden al número de secuencia
        # Con esto hay 4 bytes en total para los headers TCP
        flags = headers & 0b111
        seq = (headers >> 3)
        # El resto es el cuerpo del segmento TCP
        data = segment[4:]
        return TCPSegment(flags, seq, data)

    @staticmethod
    def create_segment(segment: TCPSegment):
        num = segment.flags | (segment.seq << 3)
        return num.to_bytes(4, byteorder='big') + segment.data

    def bind(self, address):
        self.socket.bind(address)

    def connect(self, address):
        seq = random.randint(0, 100)
        segment = TCPSegment(SYN, seq, b'')
        raw_segment = self.create_segment(segment)
        self.socket.settimeout(2)
        for intento in range(0, 5):
            try:
                self.socket.sendto(raw_segment, address)
                raw_body, addr = self.socket.recvfrom(20)
                new_segment = self.parse_segment(raw_body)
                if not (new_segment.syn and new_segment.ack) or (new_segment.seq != seq + 1): continue
                ack_segment = TCPSegment(ACK, seq=seq + 1, data=b'')
                raw_ack = self.create_segment(ack_segment)
                self.socket.sendto(raw_ack, address)
            except socket.timeout:
                if DEBUG:
                    print(f"(debug): Manejando perdidas en funcion connect [Timeout esperando SYN+ACK (intento {intento+1}/5), retransmitiendo SYN]")
                continue
            self.dest = addr
            self.num = new_segment.seq
            self.established = True
            break
        self.socket.settimeout(None)

    def accept(self):
        while True:
            raw_body, addr = self.socket.recvfrom(20)
            raw_segment = self.parse_segment(raw_body)
            if raw_segment.flags == SYN:
                break
        syn_ack_segment = TCPSegment(SYN | ACK, raw_segment.seq + 1, b'')
        raw_syn_ack = self.create_segment(syn_ack_segment)
        self.socket.settimeout(2)
        for intento in range(0, 5):
            try:
                self.socket.sendto(raw_syn_ack, addr)
                new_raw_body, new_addr = self.socket.recvfrom(20)
            except socket.timeout:
                if DEBUG:
                    print(f"(debug): Manejando perdidas en funcion accept [Timeout esperando ACK (intento {intento+1}/5), retransmitiendo SYN+ACK]")
                continue
            new_raw_segment = self.parse_segment(new_raw_body)
            es_ack = (new_raw_segment.flags == ACK and new_raw_segment.seq == syn_ack_segment.seq)
            es_datos = (new_raw_segment.flags == 0)
            if not (es_ack or es_datos): continue
            if es_datos and DEBUG:
                print(f"(debug): Manejando perdidas en funcion accept [Detectada perdida de ultimo ACK del cliente, recibido paquete de datos]")
            new_socket = SocketTCP()
            new_socket.socket = self.socket
            new_socket.dest = new_addr
            new_socket.num = syn_ack_segment.seq
            self.num = syn_ack_segment.seq
            self.established = True
            new_socket.established = True
            self.socket.settimeout(None)
            return new_socket, new_addr

    def send(self, message: bytes):
        if not self.established: return
        segment = TCPSegment(0, self.num, len(message).to_bytes(4, byteorder='big'))
        raw_segment = self.create_segment(segment)
        self.socket.settimeout(2)
        s = False
        seq = self.num
        for intento in range(0, 5):
            try:
                self.socket.sendto(raw_segment, self.dest)
                raw_body, _ = self.socket.recvfrom(20)
                new_segment = self.parse_segment(raw_body)
                if new_segment.flags == ACK and new_segment.seq == seq + 4:
                    s = new_segment.seq == seq + 4
                    break
            except socket.timeout:
                if DEBUG:
                    print(f"(debug): Manejando perdidas en funcion send [Timeout esperando ACK de longitud (intento {intento+1}/5), retransmitiendo]")
                pass
        if not s:
            self.socket.settimeout(None)
            return
        else:
            for i in range(0, len(message), 16):
                g = False
                for intento in range(0, 5):
                    try:
                        body_chunk = message[i:i+16]
                        segm = TCPSegment(0, seq + 4 + i, body_chunk)
                        raw_segm = self.create_segment(segm)
                        self.socket.sendto(raw_segm, self.dest)
                        raw_body, _ = self.socket.recvfrom(20)
                        new_segment = self.parse_segment(raw_body)
                        g = (new_segment.flags == ACK and new_segment.seq == seq + 4 + i + len(body_chunk))
                        if g: break
                    except socket.timeout:
                        if DEBUG:
                            print(f"(debug): Manejando perdidas en funcion send [Timeout esperando ACK de chunk (offset {i}, intento {intento+1}/5), retransmitiendo]")
                        pass
                if not g:
                    self.socket.settimeout(None)
                    return
        self.num += 4 + len(message)
        self.socket.settimeout(None)

    def recv(self, buff_size: int):
        if not self.established: return
        if self.received_bytes == 0:
            raw_body, addr = self.socket.recvfrom(20)
            segment = self.parse_segment(raw_body)
            message_length = int.from_bytes(segment.data, byteorder='big')
            new_segment = TCPSegment(ACK, segment.seq + 4, b'')
            raw_segment = self.create_segment(new_segment)
            self.socket.sendto(raw_segment, addr)
            min_bytes = min(message_length, buff_size)
            buffer = b""
            while len(buffer) < min_bytes:
                body, _ = self.socket.recvfrom(20)
                s = self.parse_segment(body)
                esperado = segment.seq + 4 + len(buffer)
                if s.seq == esperado:
                    buffer += s.data
                elif DEBUG:
                    print(f"(debug): Manejando perdidas en funcion recv [Segmento duplicado (seq={s.seq}, esperado={esperado}), reenviando ACK acumulado]")
                new_segment = TCPSegment(ACK, segment.seq + 4 + len(buffer), b'')
                raw_segment = self.create_segment(new_segment)
                self.socket.sendto(raw_segment, addr)
            self.num = segment.seq + 4 + len(buffer)
            self.last_message_length = message_length
            self.received_bytes = len(buffer)
            if self.received_bytes >= buff_size:
                self.remaining_msg = buffer[buff_size:]
                buffer = buffer[:buff_size]
            if self.received_bytes >= self.last_message_length and len(self.remaining_msg) == 0:
                self.received_bytes = 0
                self.last_message_length = 0
            return buffer
        else:
            min_bytes = min(self.last_message_length - self.received_bytes, buff_size - len(self.remaining_msg))
            buffer = b""
            while len(buffer) < min_bytes:
                body, addr = self.socket.recvfrom(20)
                s = self.parse_segment(body)
                esperado = self.num + len(buffer)
                if s.seq == esperado:
                    buffer += s.data
                elif DEBUG:
                    print(f"(debug): Manejando perdidas en funcion recv [Segmento duplicado (seq={s.seq}, esperado={esperado}), reenviando ACK acumulado]")
                new_segment = TCPSegment(ACK, self.num + len(buffer), b'')
                raw_segment = self.create_segment(new_segment)
                self.socket.sendto(raw_segment, addr)
            self.num += len(buffer)
            self.received_bytes += len(buffer)
            total_datos = self.remaining_msg + buffer
            self.remaining_msg = b""
            if len(total_datos) >= buff_size:
                self.remaining_msg = total_datos[buff_size:]
                total_datos = total_datos[:buff_size]
            if self.received_bytes >= self.last_message_length and len(self.remaining_msg) == 0:
                self.received_bytes = 0
                self.last_message_length = 0
            return total_datos

    def _close_conn(self):
        self.dest = ("", 0)
        self.established = False
        self.num = 0
        self.received_bytes = 0
        self.remaining_msg = b""
        self.last_message_length = 0
        try:
            self.socket.settimeout(None)
            self.socket.close()
        except Exception:
            pass

    def close(self):
        if not self.established or self.dest == ("", 0) or not self.dest[0]:
            self._close_conn()
            return
        segment = TCPSegment(FIN, self.num, b'')
        raw_segment = self.create_segment(segment)
        try:
            self.socket.settimeout(2)
        except Exception:
            self._close_conn()
            return
        raw_body = None
        keep = False
        for intento in range(0, 3):
            try:
                self.socket.sendto(raw_segment, self.dest)
                raw_body, _ = self.socket.recvfrom(20)
                keep = True
                break
            except socket.timeout:
                if DEBUG:
                    print(f"(debug): Manejando perdidas en funcion close [Timeout esperando FIN+ACK (intento {intento+1}/3), retransmitiendo FIN]")
                pass
        if not keep:
            if DEBUG:
                print(f"(debug): Manejando perdidas en funcion close [Superado maximo de 3 timeouts sin respuesta a FIN, asumiendo conexion cerrada]")
            self._close_conn()
            return
        new_segment = self.parse_segment(raw_body)
        if (not (new_segment.fin and new_segment.ack)) or new_segment.seq != segment.seq + 1: return
        final_segment = TCPSegment(ACK, new_segment.seq + 1, b'')
        raw_final_segment = self.create_segment(final_segment)
        for _ in range(0, 3):
            self.socket.sendto(raw_final_segment, self.dest)
            time.sleep(2)
        self._close_conn()

    def recv_close(self):
        raw_body, _ = self.socket.recvfrom(20)
        segment = self.parse_segment(raw_body)
        if segment.flags != FIN: return
        new_segment = TCPSegment(FIN | ACK, segment.seq + 1, b'')
        raw_segment = self.create_segment(new_segment)
        self.socket.sendto(raw_segment, self.dest)
        self.socket.settimeout(2)
        final_body = None
        for intento in range(0, 3):
            try:
                final_body, _ = self.socket.recvfrom(20)
                final_segment = self.parse_segment(final_body)
                if final_segment.flags == ACK and final_segment.seq == new_segment.seq + 1:
                    break
            except socket.timeout:
                if DEBUG:
                    print(f"(debug): Manejando perdidas en funcion recv_close [Timeout esperando ultimo ACK (intento {intento+1}/3)]")
                pass
        if final_body is None and DEBUG:
            print(f"(debug): Manejando perdidas en funcion recv_close [Superado maximo de 3 timeouts sin ultimo ACK, asumiendo conexion cerrada]")
        self._close_conn()