# test_stability.py
#
# Day15：稳定性测试
#
# 目的：
# 在同一条 TCP 连接中连续发送大量 HEARTBEAT，
# 检查服务端是否出现：
# 1. 中途断线
# 2. 响应错误
# 3. 偶发失败
# 4. 长时间运行后异常


from client.tcp_client import DeviceClient
from client.protocol import HEARTBEAT


def test_1000_heartbeat_requests():
    """
    连续发送500次心跳。

    验收要求：
    500次请求全部返回 code=0。
    """

    # 使用同一个 TCP Client。
    #
    # 这里不是每次请求都重新建立连接，
    # 而是在一条连接上连续执行500次业务请求，
    # 用来验证持续通信是否稳定。
    with DeviceClient(timeout=2) as c:

        # 连续执行500次
        for i in range(1000):

            # 发送HEARTBEAT
            resp = c.request(
                HEARTBEAT
            )

            # 每次请求都必须成功。
            #
            # 只要其中任何一次code不是0，
            # pytest就会立即判定当前测试失败。
            assert resp["code"] == "0"

            # 每100次打印一次进度，
            # 避免500次全部打印导致终端太乱。
            if (i + 1) % 200 == 0:
                print(
                    f"completed "
                    f"{i + 1}/1000 requests"
                )
