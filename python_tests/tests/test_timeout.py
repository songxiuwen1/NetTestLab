# test_timeout.py
#
# Day 13：客户端超时 + 服务恢复测试
#
# 测试目标：
# 1. 服务端响应过慢时，客户端应该按预期超时
# 2. 客户端超时并关闭连接以后，服务端不能崩溃
# 3. 等待服务端原来的慢任务结束后，
#    再发送HEARTBEAT验证服务仍然健康


import socket
import time

import pytest


from client.tcp_client import DeviceClient

from client.protocol import (
    SLOW_RESPONSE,
    HEARTBEAT,
)


def test_client_timeout_and_server_recovery():
    """
    场景：

    客户端最大等待时间：0.2秒
    服务端故意响应时间：1秒

    所以客户端应该发生socket.timeout。

    之后等待1秒以上，
    再发送正常HEARTBEAT。

    如果仍然返回PONG，
    才能真正证明服务器没有因为异常连接而崩溃。
    """


    # --------------------------------------------------
    # 第一阶段：验证客户端超时
    # --------------------------------------------------

    # 我们明确期待出现socket.timeout。
    #
    # 所以如果真的发生timeout，
    # pytest认为这是正确结果，测试不会失败。
    with pytest.raises(socket.timeout):

        # 客户端只允许等待0.2秒
        with DeviceClient(timeout=0.2) as c:

            # 服务端故意等待1000ms，也就是1秒
            c.request(
                SLOW_RESPONSE,
                "ms=1000"
            )


    # --------------------------------------------------
    # 第二阶段：等待服务端完成原来的慢响应
    # --------------------------------------------------

    # 服务端会sleep 1秒。
    #
    # 如果存在“向已关闭Socket发送导致Server崩溃”的问题，
    # 它通常会在这一阶段暴露。
    #
    # 所以故意等待1.2秒，
    # 不能马上做健康检查。
    time.sleep(1.2)


    # --------------------------------------------------
    # 第三阶段：服务恢复性健康检查
    # --------------------------------------------------

    # 再建立一个新的TCP连接。
    #
    # 如果DeviceServer已经崩溃，
    # 这里会直接ConnectionRefused。
    with DeviceClient(timeout=2.0) as c:

        # 发送最基本的心跳请求
        resp = c.request(
            HEARTBEAT
        )

        print(
            "recovery heartbeat:",
            resp
        )

        # 必须正常返回PONG，
        # 才说明服务器在客户端超时之后仍然健康。
        assert resp["code"] == "0"

        assert resp["message"] == "PONG"
