# -*- coding:utf-8 -*-
import socket
import random
import base64
import hashlib
import re

HOST = "localhost"
PORT = 5858


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        ######################################
        # HandShake Start ####################

        raw_key = bytes(random.getrandbits(8) for _ in range(16))
        sec_ws_key = base64.b64encode(raw_key).decode("utf-8")

        req = "GET / HTTP/1.1\r\n" + \
              "Upgrade: websocket\r\n" \
              f"Host: {HOST}:{PORT}\r\n" \
              f"Origin: http://{HOST}:{PORT}\r\n" \
              f"Sec-WebSocket-Key: {sec_ws_key}\r\n" \
              "Sec-WebSocket-Version: 13\r\n" \
              "Connection: upgrade\r\n\r\n"

        s.sendall(req.encode("utf-8"))

        buffer = bytearray()

        while True:
            buffer = buffer + bytearray(s.recv(8))

            # HandShake의 맨 끝은 CRLF 두번
            if 0 <= buffer.find(b"\r\n\r\n"):
                break

        regex = re.compile("Sec-WebSocket-Accept: (.+?)\r\n")
        re_match = regex.search(buffer.decode("utf-8"))
        resp_sec_ws_acpt = re_match.group(1)

        chk_sec_ws_acpt = bytes(sec_ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11", encoding="utf-8")
        chk_sec_ws_acpt = base64.b64encode(hashlib.sha1(chk_sec_ws_acpt).digest()).decode("utf-8")

        if resp_sec_ws_acpt == chk_sec_ws_acpt:
            print("핸드쉐이크 성공 !!!")
        else:
            print("핸드쉐이크 실패 !!!")
            return False

        # HandShake End ######################
        ######################################

        # TODO: 데이터 송신 및 수신

        return True


if "__main__" == __name__:
    main()
