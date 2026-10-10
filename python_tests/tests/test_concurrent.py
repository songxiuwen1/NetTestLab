# test_concurrent.py
#
# Day14：并发测试
#
# 测试目标：
# 同时创建多个TCP客户端访问DeviceServer，
# 验证服务端在并发情况下是否仍然能够正确处理请求。


from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)


# 我们已经封装好的TCP客户端
from client.tcp_client import DeviceClient


# 今天使用最简单的HEARTBEAT作为并发请求。
#
# 原因：
# HEARTBEAT业务逻辑非常简单，
# 可以尽量把测试重点放在“并发连接和线程处理”上，
# 而不是复杂业务逻辑上。
from client.protocol import HEARTBEAT


def one_request(client_id):
    """
    一个客户端执行一次请求。

    返回：
        True  -> 请求成功
        False -> 请求失败

    client_id主要用于失败时打印是哪个客户端出问题。
    """

    try:
        # 每个并发任务都建立自己的TCP连接。
        #
        # timeout=2：
        # 如果2秒内无法完成连接或响应，
        # 就认为这次请求失败。
        with DeviceClient(timeout=2) as c:

            # 发送心跳请求
            resp = c.request(
                HEARTBEAT
            )

            # code=0代表服务端正常处理
            return resp.get("code") == "0"

    except Exception as exc:
        # 并发测试中我们暂时不让一个客户端异常
        # 直接终止整个执行过程。
        #
        # 先记录失败，然后最终统一统计成功率。
        print(
            f"client {client_id} failed:",
            repr(exc)
        )

        return False


def test_50_concurrent_clients():
    """
    同时制造50个客户端请求。

    验收标准：
    50个必须全部成功。
    """

    # 本次总客户端数量
    total = 100


    # max_workers=50表示：
    #
    # Python测试端最多同时使用50个工作线程。
    #
    # 注意：
    # 这是“制造测试负载”的线程池，
    # 不是DeviceServer内部的线程池。
    with ThreadPoolExecutor(
        max_workers=100
    ) as pool:

        # 向线程池一次提交50个任务。
        #
        # pool.submit(one_request, i)
        #
        # 表示：
        # 让某个线程执行 one_request(i)
        futures = [
            pool.submit(
                one_request,
                i
            )
            for i in range(total)
        ]


        # as_completed：
        #
        # 哪个请求先完成，
        # 就先取哪个结果。
        #
        # 不要求按照1、2、3...的顺序完成。
        results = [
            future.result()
            for future in as_completed(futures)
        ]


    # Python里：
    #
    # True 计算时等于1
    # False计算时等于0
    #
    # 所以sum(results)
    # 就是成功请求数量。
    success = sum(results)


    # 输出本次并发结果，方便观察。
    print(
        f"total={total}, "
        f"success={success}, "
        f"failed={total - success}"
    )


    # 今天首先检查正确性：
    # 50个客户端必须全部成功。
    assert success == total
