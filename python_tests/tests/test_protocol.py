# test_protocol.py
#
# Day17：自定义TCP协议测试
#
# 测试内容：
# 1. 未知Command
# 2. 错误Magic
# 3. 两帧一次发送（连续TCP字节流）
# 4. 一帧拆成两次发送
#
# 目的：
# 验证DeviceServer面对正常/异常TCP字节流时
# 都能够正确解析，并且异常请求不会拖垮整个Server。


import socket
import struct
import time


from client.protocol import (
    HEADER_FMT,
    VERSION,
    HEARTBEAT,
    pack_packet,
    recv_packet,
    parse_kv,
)


# 被测服务地址
HOST = "127.0.0.1"
PORT = 9000


def test_unknown_command_returns_400():
    """
    测试未知命令。

    0xFE没有被Server定义为合法Command，
    所以服务端应该返回错误码400。
    """

    # 建立TCP连接
    with socket.create_connection(
        (HOST, PORT),
        timeout=2
    ) as sock:

        # pack_packet仍然构造一个格式正确的协议包，
        # 但Command故意使用未知值0xFE。
        sock.sendall(
            pack_packet(
                0xFE,
                100,
                ""
            )
        )

        # 接收服务端响应
        _, _, payload = recv_packet(sock)

        # 把key=value字符串转为字典
        resp = parse_kv(payload)

        # 未知Command应该被正确拒绝
        assert resp["code"] == "400"


def test_bad_magic_does_not_crash_server():
    """
    测试错误Magic。

    错误协议连接可以被Server关闭，
    但整个DeviceServer进程不能崩。
    """

    # 手工构造协议Header。
    #
    # 正常Magic应该是0xAA55，
    # 这里故意写成0x1234。
    bad_header = struct.pack(
        HEADER_FMT,
        0x1234,       # 错误Magic
        VERSION,      # Version仍然正确
        HEARTBEAT,    # Command仍然正确
        1,            # Sequence
        0,            # Payload Length
    )

    # 第一次连接：
    # 发送错误Magic。
    with socket.create_connection(
        (HOST, PORT),
        timeout=2
    ) as sock:

        sock.sendall(
            bad_header
        )

    # 给Server一点时间清理异常连接
    time.sleep(0.1)

    # 第二次重新建立正常连接。
    #
    # 如果还能得到PONG，
    # 就证明刚才的非法协议没有把整个Server搞崩。
    with socket.create_connection(
        (HOST, PORT),
        timeout=2
    ) as sock:

        sock.sendall(
            pack_packet(
                HEARTBEAT,
                2,
                ""
            )
        )

        _, _, payload = recv_packet(sock)

        resp = parse_kv(payload)

        assert resp["message"] == "PONG"


def test_two_packets_sent_together_are_both_parsed():
    """
    一次sendall发送两条完整协议帧。

    目的：
    验证TCP连续字节流中连续出现两帧时，
    Server能按照Header + Length正确拆出两条消息。
    """

    # 第一帧
    frame1 = pack_packet(
        HEARTBEAT,
        11,
        ""
    )

    # 第二帧
    frame2 = pack_packet(
        HEARTBEAT,
        12,
        ""
    )

    with socket.create_connection(
        (HOST, PORT),
        timeout=2
    ) as sock:

        # 重点：
        #
        # 两帧直接拼在一起，
        # 通过一次sendall发出去。
        sock.sendall(
            frame1 + frame2
        )

        # Server应该返回两个独立响应
        _, seq1, payload1 = recv_packet(sock)

        _, seq2, payload2 = recv_packet(sock)

        # 第一条响应必须对应Sequence=11
        assert seq1 == 11

        assert (
            parse_kv(payload1)["message"]
            == "PONG"
        )

        # 第二条响应必须对应Sequence=12
        assert seq2 == 12

        assert (
            parse_kv(payload2)["message"]
            == "PONG"
        )


def test_one_packet_split_into_two_sends():
    """
    把一个12字节HEARTBEAT Header拆成两次send。

    目的：
    验证Server的RecvExact能够把分段到达的数据
    重新收完整，而不是假设一次recv就得到完整消息。
    """

    # 创建一个完整HEARTBEAT协议包
    frame = pack_packet(
        HEARTBEAT,
        21,
        ""
    )

    # 在第5个字节的位置切开
    cut = 5


    with socket.create_connection(
        (HOST, PORT),
        timeout=2
    ) as sock:

        # 第一次只发送前5字节
        sock.sendall(
            frame[:cut]
        )

        # 故意停一下，
        # 让“分成两段到达”更加明显。
        time.sleep(0.05)

        # 第二次发送剩余数据
        sock.sendall(
            frame[cut:]
        )

        # Server仍然应该能够正确恢复完整协议包
        _, seq, payload = recv_packet(sock)

        assert seq == 21

        assert (
            parse_kv(payload)["message"]
            == "PONG"
        )
