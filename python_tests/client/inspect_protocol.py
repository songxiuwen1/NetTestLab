# inspect_protocol.py
# 目的：
# 亲眼观察一个协议包到底有多少字节，
# 并把每个字节用十六进制打印出来。

from protocol import (
    HEADER_SIZE,
    HEARTBEAT,
    pack_packet,
)


# 构造一个心跳包：
# Command = HEARTBEAT
# Sequence = 1
# Payload为空
packet = pack_packet(
    command=HEARTBEAT,
    sequence=1,
    payload=""
)


# 打印固定Header大小
print(
    "HEADER_SIZE =",
    HEADER_SIZE
)


# 打印整个协议包长度。
# 因为Payload为空，所以应该也是12字节。
print(
    "packet length =",
    len(packet)
)


# .hex(" ") 会把bytes以十六进制显示，
# 更接近Wireshark以后看到的网络数据。
print(
    "packet hex =",
    packet.hex(" ")
)
