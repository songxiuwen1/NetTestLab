# test_boundary.py
#
# Day 10:
# 边界值测试
#
# 测试目标：
# 验证服务器是否正确处理：
# 1. 合法边界
# 2. 非法边界


import pytest

from client.tcp_client import DeviceClient

from client.protocol import SET_PARAM



# ------------------------------------------------
# speed边界测试
# ------------------------------------------------


@pytest.mark.parametrize(
    "speed, expected",
    [

        # speed=-1
        # 小于允许范围
        # 应该失败
        (-1, False),


        # speed=0
        # 最小合法值
        (0, True),


        # speed=5000
        # 最大合法值
        (5000, True),


        # speed=5001
        # 超过最大值
        (5001, False),
    ]
)
def test_speed_boundary(speed, expected):

    """
    测试speed参数边界

    speed范围:
    0~5000
    """


    with DeviceClient() as c:


        # 构造参数字符串
        #
        # 协议格式：
        # speed=xxx;duration=xxx
        param = (
            f"speed={speed};duration=2"
        )


        # 发送设置参数请求
        resp = c.request(
            SET_PARAM,
            param
        )


        print(
            "speed:",
            speed,
            "response:",
            resp
        )


        if expected:

            # 期望成功
            assert resp["code"] == "0"

        else:

            # 期望失败
            assert resp["code"] != "0"




# ------------------------------------------------
# duration边界测试
# ------------------------------------------------


@pytest.mark.parametrize(
    "duration, expected",
    [

        # 小于1秒
        (0, False),


        # 最小合法
        (1, True),


        # 最大合法
        (60, True),


        # 超过最大
        (61, False),

    ]
)
def test_duration_boundary(duration, expected):


    """
    测试duration范围

    duration:
    1~60
    """


    with DeviceClient() as c:


        param = (
            f"speed=1000;"
            f"duration={duration}"
        )


        resp = c.request(
            SET_PARAM,
            param
        )


        print(
            "duration:",
            duration,
            resp
        )


        if expected:

            assert resp["code"] == "0"

        else:

            assert resp["code"] != "0"
