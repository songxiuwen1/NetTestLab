# test_smoke.py
#
# 冒烟测试：
# 只验证系统最核心的通信链路是否可用。
#
# 今天测试：
# 1. HEARTBEAT
# 2. GET_STATUS


# 导入我们封装好的 TCP 客户端
from client.tcp_client import DeviceClient


# 导入协议命令字
from client.protocol import (
    HEARTBEAT,
    GET_STATUS,
)


def test_heartbeat():
    """
    验证心跳功能。

    预期：
    HEARTBEAT -> PONG
    """

    # 建立TCP连接；
    # with结束后自动关闭Socket。
    with DeviceClient() as c:

        # 向C++ Server发送 HEARTBEAT 命令
        resp = c.request(
            HEARTBEAT
        )


        # 服务端应该返回成功码0
        assert resp["code"] == "0"


        # 心跳响应应该是PONG
        assert resp["message"] == "PONG"


def test_get_status():
    """
    验证查询设备状态的基本功能。
    """

    # 新建一个独立TCP连接
    with DeviceClient() as c:

        # 请求设备当前状态
        resp = c.request(
            GET_STATUS
        )


        # 请求必须成功
        assert resp["code"] == "0"


        # 当前设备状态必须属于
        # 系统定义的合法状态之一
        assert resp["state"] in {
            "IDLE",
            "RUNNING",
            "FINISHED",
        }
