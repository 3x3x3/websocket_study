# -*- coding:utf-8 -*-
import socket
import re
import base64
import hashlib

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
            resp_key = re_match.group(1) + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            cipher_key = base64.b64encode(hashlib.sha1(bytes(resp_key, encoding="utf-8")).digest()).decode("utf-8")

            resp = "HTTP/1.1 101 Switching Protocols\r\n" + \
                   "Upgrade: websocket\r\n" + \
                   "Connection: Upgrade\r\n" + \
                   f"Sec-WebSocket-Accept: {cipher_key}\r\n\r\n"

            conn.sendall(resp.encode("utf-8"))

            # HandShake End ######################
            ######################################

            # TODO: 데이터 송신 및 수신


if "__main__" == __name__:
    main()
