# tcp_client.py
#
# 作用：
# 封装 TCP 连接、Sequence 生成、协议发送和响应接收。
#
# 这样 pytest 测试代码以后不需要每条用例都重复写：
# socket()
# connect()
# sendall()
# recv()
# close()


import itertools
import socket


# 从 protocol.py 导入已经写好的协议函数
from .protocol import (
    pack_packet,
    recv_packet,
    parse_kv,
)


# 创建一个不断递增的序列号生成器：
#
# 1, 2, 3, 4, 5...
#
# 每发一个请求，使用不同 Sequence，
# 方便关联请求和响应。
_seq = itertools.count(1)


class DeviceClient:
    """
    DeviceServer 的 Python TCP 客户端。

    默认连接：
    127.0.0.1:9000
    """

    def __init__(
        self,
        host="127.0.0.1",
        port=9000,
        timeout=2.0
    ):
        # 创建 IPv4 + TCP Socket
        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )


        # 设置 Socket 超时时间。
        #
        # 如果服务器2秒都没有响应，
        # Python不会无限等待，而是抛出 timeout。
        #
        # 后面做“超时测试”时会专门使用这个机制。
        self.sock.settimeout(timeout)


        # 主动连接 C++ DeviceServer
        self.sock.connect(
            (host, port)
        )


    def request(
        self,
        command: int,
        payload: str = ""
    ) -> dict:
        """
        发送一次请求，并等待一次响应。
        """

        # 获取本次请求的唯一 Sequence
        seq = next(_seq)


        # pack_packet() 会生成：
        #
        # Header(12字节) + Payload
        #
        # sendall() 再把完整二进制包通过TCP发送
        self.sock.sendall(
            pack_packet(
                command,
                seq,
                payload
            )
        )


        # 等待服务端响应。
        #
        # recv_packet() 会：
        # 1. 先收12字节Header
        # 2. 解析Length
        # 3. 再收Payload
        _, resp_seq, text = recv_packet(
            self.sock
        )


        # 服务端返回的 Sequence
        # 必须和本次请求相同。
        #
        # 例如：
        # 发送 seq=5
        # 就必须收到 resp_seq=5
        if resp_seq != seq:
            raise AssertionError(
                f"sequence mismatch: "
                f"send={seq}, recv={resp_seq}"
            )


        # 把：
        #
        # code=0;message=PONG
        #
        # 转换成：
        #
        # {
        #   "code": "0",
        #   "message": "PONG"
        # }
        return parse_kv(text)


    def close(self):
        """
        主动关闭 Socket。
        """

        try:
            self.sock.close()

        except OSError:
            # 即使Socket已经被关闭，
            # 这里也不要因为再次关闭而影响测试清理。
            pass


    def __enter__(self):
        """
        支持：

        with DeviceClient() as c:
            ...

        进入 with 时返回当前客户端对象。
        """

        return self


    def __exit__(
        self,
        exc_type,
        exc,
        tb
    ):
        """
        离开 with 代码块时自动关闭 Socket。

        即使测试中 assert 失败或出现异常，
        close() 仍会被执行。
        """

        self.close()
