# send_bad_magic.py
#
# Day16：故意构造一个Magic错误的二进制协议包。
#
# 目的不是“正常使用系统”，
# 而是制造一个稳定可复现的错误，
# 然后练习通过Server日志定位问题。


import socket
import struct


# 被测服务器
HOST = "127.0.0.1"
PORT = 9000


# 正常协议头格式：
#
# !  -> 网络字节序
# H  -> Magic，2字节
# B  -> Version，1字节
# B  -> Command，1字节
# I  -> Sequence，4字节
# I  -> Length，4字节
HEADER_FMT = "!HBBII"


# 故意使用错误Magic。
#
# 正常应该：
# 0xAA55
#
# 我们这里故意：
# 0x1234
BAD_MAGIC = 0x1234


# 当前协议版本仍然保持正确，
# 这样就能把问题集中在Magic字段。
VERSION = 1


# HEARTBEAT命令
COMMAND = 0x06


# 请求序列号
SEQUENCE = 999


# 本次没有Payload，
# 所以长度是0。
LENGTH = 0


# 按照12字节协议头格式打包。
bad_header = struct.pack(
    HEADER_FMT,
    BAD_MAGIC,
    VERSION,
    COMMAND,
    SEQUENCE,
    LENGTH,
)


print(
    "send bytes:",
    bad_header.hex(" ")
)


# 建立TCP连接。
with socket.create_connection(
    (HOST, PORT),
    timeout=2
) as sock:

    # 发送Magic错误的Header。
    sock.sendall(
        bad_header
    )


print(
    "bad magic packet sent"
)
