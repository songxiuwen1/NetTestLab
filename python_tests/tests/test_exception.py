# test_exception.py
#
# Day 11:
# 异常输入测试
#
# 目标：
# 验证非法请求不会导致系统异常
# 并且返回正确错误码


import pytest


from client.tcp_client import DeviceClient


from client.protocol import SET_PARAM



@pytest.mark.parametrize(
    "param",
    [

        # --------------------------------
        # 缺少duration
        # --------------------------------
        "speed=1000",


        # --------------------------------
        # speed不是数字
        # --------------------------------
        "speed=abc;duration=2",


        # --------------------------------
        # duration不是数字
        # --------------------------------
        "speed=1000;duration=test",


        # --------------------------------
        # 空字符串
        # --------------------------------
        "",

    ]
)
def test_invalid_parameter(param):

    """
    测试非法参数输入

    期望：
    服务端拒绝请求

    不能：
    崩溃
    """

    with DeviceClient() as c:


        # 发送异常参数
        resp = c.request(
            SET_PARAM,
            param
        )


        print(
            "input:",
            param,
            "response:",
            resp
        )


        # 错误情况下：
        # code不应该等于0
        #
        # 0代表成功
        assert resp["code"] != "0"
