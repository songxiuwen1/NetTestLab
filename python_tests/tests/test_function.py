# test_function.py
#
# Day 9 功能测试
#
# 测试目标：
# 1. 把设备恢复到 IDLE
# 2. 设置合法参数
# 3. 启动任务
# 4. 不断查询状态
# 5. 验证任务最终进入 FINISHED
# 6. 验证 progress=100、result=OK


import time


# DeviceClient 封装了：
# socket连接、协议打包、发送、接收和关闭
from client.tcp_client import DeviceClient


# 导入今天需要使用的协议命令
from client.protocol import (
    SET_PARAM,
    START_TASK,
    GET_STATUS,
    STOP_TASK,
)


def test_set_param_start_and_finish():
    """
    验证完整业务流程：

    IDLE
      ↓ SET_PARAM
    参数设置成功
      ↓ START_TASK
    RUNNING
      ↓ 等待任务执行
    FINISHED
    """

    # 创建TCP客户端。
    #
    # with结束时会自动关闭Socket，
    # 即使测试失败也能正确释放连接。
    with DeviceClient() as c:

        # -------------------------------------------------
        # 第1步：先恢复设备状态
        # -------------------------------------------------

        # 为什么先STOP_TASK？
        #
        # 因为我们不知道前一条测试
        # 是否可能留下 RUNNING 状态。
        #
        # 自动化测试应该尽量让每条用例
        # 从可预测的初始状态开始。
        c.request(STOP_TASK)


        # -------------------------------------------------
        # 第2步：设置合法参数
        # -------------------------------------------------

        # speed=1200：
        # 在合法范围 [0,5000] 内
        #
        # duration=2：
        # 任务模拟执行2秒
        resp = c.request(
            SET_PARAM,
            "speed=1200;duration=3"
        )

        # 打印响应，方便现在学习时观察
        print(
            "SET_PARAM response:",
            resp
        )

        # 设置参数必须成功
        assert resp["code"] == "0"


        # -------------------------------------------------
        # 第3步：启动任务
        # -------------------------------------------------

        resp = c.request(
            START_TASK
        )

        print(
            "START_TASK response:",
            resp
        )

        # 启动任务应该成功
        assert resp["code"] == "0"


        # -------------------------------------------------
        # 第4步：轮询状态
        # -------------------------------------------------

        # 当前任务 duration=2秒。
        #
        # 我们最多允许它4秒完成，
        # 给系统留一定余量。
        #
        # 非常重要：
        # 自动化等待必须有最大时间，
        # 不能无限循环。
        deadline = time.time() + 4


        # 保存最后一次查询结果
        last = None


        # 当前时间没超过截止时间，
        # 就继续查询设备状态。
        while time.time() < deadline:

            # 查询当前设备状态
            last = c.request(
                GET_STATUS
            )

            # 输出当前状态和进度，
            # 因为本次运行使用 pytest -s，
            # 所以终端可以直接看到。
            print(
                "GET_STATUS:",
                last
            )


            # 如果任务已经完成，
            # 不必继续等待，直接退出循环。
            if last["state"] == "FINISHED":
                break


            # 当前还没有完成，
            # 等0.2秒后再查询。
            #
            # 如果没有sleep而疯狂查询，
            # 会产生大量无意义请求并占用CPU。
            time.sleep(0.2)


        # -------------------------------------------------
        # 第5步：验证最终结果
        # -------------------------------------------------

        # 至少应该成功查询过一次状态
        assert last is not None


        # 最终必须进入 FINISHED
        assert last["state"] == "FINISHED"


        # 完成时进度应该100%
        assert last["progress"] == "100"


        # 模拟设备正常完成后的结果应为OK
        assert last["result"] == "OK"
