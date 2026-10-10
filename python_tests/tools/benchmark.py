# benchmark.py
#
# Day14 / Day15都会使用的简单性能采集工具。
#
# 注意：
# 它的主要任务不是判定PASS/FAIL，
# 而是记录并发请求下的性能数据。


import statistics
import time
# math.ceil 用于计算P95对应的排序位置
import math

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)


from client.tcp_client import DeviceClient
from client.protocol import HEARTBEAT


def one_request(request_id):
    """
    执行一次HEARTBEAT，
    同时测量这次请求耗时。
    """

    # perf_counter适合测量经过时间，
    # 精度比普通time.time更适合性能计时。
    start = time.perf_counter()


    # 默认认为失败
    ok = False


    try:
        # 最多等待3秒
        with DeviceClient(timeout=3) as c:

            # 发送HEARTBEAT
            resp = c.request(
                HEARTBEAT
            )

            # code=0代表请求成功
            ok = (
                resp.get("code") == "0"
            )

    except Exception as exc:
        # 性能采集时某个请求失败，
        # 不立刻终止全部任务，
        # 最后统一统计成功率。
        print(
            f"request {request_id} failed:",
            repr(exc)
        )

        ok = False


    # 计算本次请求持续时间。
    #
    # *1000：
    # 从秒转换成毫秒。
    latency_ms = (
        time.perf_counter() - start
    ) * 1000


    # 返回：
    #
    # 是否成功
    # +
    # 延迟
    return ok, latency_ms


def run(
    total=500,
    workers=50
):
    """
    total：
        一共发送多少次请求。

    workers：
        最多同时有多少个客户端工作线程。
    """


    # 整个benchmark开始时间
    started = time.perf_counter()


    # 保存所有请求结果
    rows = []


    # 创建客户端侧并发线程池
    with ThreadPoolExecutor(
        max_workers=workers
    ) as pool:


        # 一次提交total个请求
        futures = [
            pool.submit(
                one_request,
                i
            )
            for i in range(total)
        ]


        # 谁先完成就先记录谁
        for future in as_completed(futures):
            rows.append(
                future.result()
            )


    # 整个测试总耗时
    elapsed = (
        time.perf_counter()
        - started
    )


    # 单独提取所有延迟
    latencies = [
        row[1]
        for row in rows
    ]

    # --------------------------------------------------
    # 计算 P95 延迟
    # --------------------------------------------------

    # 先把所有请求延迟从小到大排序
    sorted_latencies = sorted(
        latencies
    )


    # P95的直观理解：
    #
    # 把所有延迟排序以后，
    # 找到大约第95%位置对应的延迟。
    #
    # 例如有100个请求：
    # P95大致就是第95个请求对应的延迟。
    p95_index = (
        math.ceil(
            len(sorted_latencies) * 0.95
       )
       - 1
    )


    # 根据索引得到P95
    p95_latency = sorted_latencies[
        p95_index
    ]


    # 统计成功数量
    success = sum(
        1
        for row in rows
        if row[0]
    )


    # ------------------------------
    # 输出测试条件和结果
    # ------------------------------

    print("=" * 46)

    print("Concurrent Benchmark")

    print("=" * 46)


    # 客户端并发线程数
    print(
        f"workers          : {workers}"
    )


    # 请求总数
    print(
        f"total requests   : {total}"
    )


    # 成功数量
    print(
        f"success          : {success}"
    )


    # 成功率
    print(
        f"success rate     : "
        f"{success / total * 100:.2f}%"
    )


    # 所有请求平均延迟
    print(
        f"average latency  : "
        f"{statistics.mean(latencies):.2f} ms"
    )

    # 输出P95延迟
    print(
       f"P95 latency      : "
       f"{p95_latency:.2f} ms"
    )


    # 最慢请求
    print(
        f"max latency      : "
        f"{max(latencies):.2f} ms"
    )


    # 吞吐量：
    #
    # 总请求数 / 总运行时间
    #
    # 单位：
    # requests per second
    print(
        f"throughput       : "
        f"{total / elapsed:.2f} req/s"
    )


if __name__ == "__main__":

    # 默认：
    #
    # 500次总请求
    # 50个并发客户端线程
    run(
        total=500,
        workers=50
    )
