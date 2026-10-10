# test_disconnect.py
#
# Day 13：连接中途断开测试
#
# 测试目标：
# 客户端只发送一部分协议Header以后突然断开，
# C++ Server应该正确结束这个异常连接，
# 不能导致整个服务器进程崩溃。


import socket
import time


# 导入协议工具
from client.protocol import (
    pack_packet,
    HEARTBEAT,
    recv_packet,
    parse_kv,
)


# 被测服务器地址
HOST = "127.0.0.1"

# 被测服务器TCP端口
PORT = 9000


def test_partial_packet_then_disconnect_does_not_crash_server():
    """
    测试流程：

    1. 建立TCP连接
    2. 构造完整心跳协议包
    3. 故意只发送前5字节
    4. 突然关闭客户端连接
    5. 再建立一个正常连接
    6. 发送正常HEARTBEAT
    7. 如果还能收到PONG，证明Server没有被异常连接拖垮
    """


    # --------------------------------------------------
    # 第一阶段：制造异常连接
    # --------------------------------------------------

    # 建立到C++ DeviceServer的TCP连接。
    #
    # timeout=2 表示连接操作最多等待2秒。
    s = socket.create_connection(
        (HOST, PORT),
        timeout=2
    )


    # 构造一个正常的完整心跳协议包。
    #
    # 正常情况下：
    # frame长度应该是12字节，
    # 因为HEARTBEAT没有Payload。
    frame = pack_packet(
        HEARTBEAT,
        1,
        ""
    )


    # 故意只发送前5个字节。
    #
    # frame[:5]
    # 表示Python切片：
    # 从第0个字节开始，只取前5个。
    #
    # 服务端本来需要完整12字节Header，
    # 所以这一定是不完整的数据。
    s.sendall(
        frame[:5]
    )


    # 数据只发了一半就突然断开。
    #
    # 这模拟：
    # 网络掉线、客户端崩溃、
    # 进程异常退出等情况。
    s.close()


    # 给服务器一点时间处理断线。
    #
    # 这里只等待0.1秒，
    # 不是业务逻辑的一部分，
    # 只是让异常连接的清理完成。
    time.sleep(0.1)


    # --------------------------------------------------
    # 第二阶段：健康检查
    # --------------------------------------------------

    # 重新建立一个新的正常TCP连接。
    #
    # 如果前面的异常连接把服务器搞崩了，
    # 这里就会连接失败。
    with socket.create_connection(
        (HOST, PORT),
        timeout=2
    ) as c:


        # 发送一个完整、合法的HEARTBEAT。
        #
        # 使用新的Sequence = 2。
        c.sendall(
            pack_packet(
                HEARTBEAT,
                2,
                ""
            )
        )


        # 接收服务端正常响应。
        _, _, payload = recv_packet(c)


        # 把：
        #
        # code=0;message=PONG
        #
        # 转换成Python字典。
        resp = parse_kv(payload)


        print(
            "health check response:",
            resp
        )


        # 最终健康检查必须仍然返回PONG。
        #
        # 如果成功，说明前面的半包+断线
        # 没有把整个Server搞崩。
        assert resp["message"] == "PONG"
