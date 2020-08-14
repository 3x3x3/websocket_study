# -*- coding:utf-8 -*-
import socket
import re
import base64
import hashlib
import struct

MAGIC_NUMBER = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
HOST = ""
PORT = 5858


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        conn, addr = s.accept()

        with conn:

            ######################################
            # HandShake Start ####################
            buffer = bytearray()

            while True:
                buffer = buffer + bytearray(conn.recv(8))

                # HandShake의 맨 끝은 CRLF 두번
                if 0 <= buffer.find(b"\r\n\r\n"):
                    break

            regex = re.compile("Sec-WebSocket-Key: (.+?)\r\n")
            re_match = regex.search(buffer.decode("utf-8"))
            resp_key = re_match.group(1) + MAGIC_NUMBER
            cipher_key = base64.b64encode(hashlib.sha1(bytes(resp_key, encoding="utf-8")).digest()).decode("utf-8")

            resp = "HTTP/1.1 101 Switching Protocols\r\n" + \
                   "Upgrade: websocket\r\n" + \
                   "Connection: Upgrade\r\n" + \
                   f"Sec-WebSocket-Accept: {cipher_key}\r\n\r\n"

            conn.sendall(resp.encode("utf-8"))

            # HandShake End ######################
            ######################################

            ######################################
            # Receive Data From Client Start #####

            first_byte = conn.recv(1)

            if 0 == first_byte:
                print("연결 끊김")
                return False

            first_byte = bytearray(first_byte)[0]
            second_byte = bytearray(conn.recv(1))[0]

            # fin: 1=마지막, 0=데이터 더있음
            fin = (0xFF & first_byte) >> 7

            # opcode: 0=연속, 1=문자열, 2=바이너리, 8=접속종료, 9=ping, 10=pong
            opcode = (0x0F & first_byte)

            # mask: 1=마스크처리됨
            mask = (0xFF & second_byte) >> 7

            # payload_len: 0~125=원래값, 126=2Bytes를 더 읽어온값, 127=8Bytes를 더 읽어온값
            payload_len = (0x7F & second_byte)

            data: bytearray

            if 3 > opcode:
                # Get Payload Length
                if payload_len == 126:
                    payload_len = struct.unpack_from(">H", bytearray(conn.recv(2, socket.MSG_WAITALL)))[0]
                elif payload_len == 127:
                    payload_len = struct.unpack_from(">Q", bytearray(conn.recv(8, socket.MSG_WAITALL)))[0]

                if 1 == mask:
                    masking_key = bytearray(conn.recv(4, socket.MSG_WAITALL))
                    masked_data = bytearray(conn.recv(payload_len, socket.MSG_WAITALL))
                    data = bytearray([masked_data[i] ^ masking_key[i % 4] for i in range(len(masked_data))])
                else:
                    data = bytearray(conn.recv(payload_len, socket.MSG_WAITALL))

            elif 8 == opcode:
                print("접속 종료")
                return False

            else:
                print("Ping/Pong 구현 안한다")
                return False

            rcv_data = data.decode("utf-8")
            print("수신:", rcv_data)

            # Receive Data From Client End #######
            ######################################

            ######################################
            # Send Data To Client Start ##########

            data = bytearray(rcv_data.encode("utf-8"))

            try:
                header: bytearray = bytearray()

                # payload가 126일때 extended_payload_len을 2바이트 가지는데 이때 최대 값이 65535
                payload_length = len(data)

                if 125 >= payload_length:
                    header.append(0x80 | 0x1)
                    header.append(payload_length)

                elif 126 <= payload_length <= 65535:
                    header.append(0x80 | 0x1)
                    header.append(0x7e)
                    header.extend(struct.pack(">H", payload_length))

                elif payload_length < 18446744073709551616:
                    header.append(0x80 | 0x1)
                    header.append(0x7f)
                    header.extend(struct.pack(">Q", payload_length))

                else:
                    print("너무크다")
                    return False

                conn.sendall(header + data)
                print("보내기 완료")

            except Exception as e:
                print("예외 발생")
                print(str(e))
                return False

            # Send Data To Client End ############
            ######################################


if "__main__" == __name__:
    main()
