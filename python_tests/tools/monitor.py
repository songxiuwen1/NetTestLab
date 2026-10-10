# monitor.py
#
# Day15：DeviceServer资源监控
#
# 目的：
# 周期性观察C++服务端：
# 1. CPU使用率
# 2. RSS内存
#
# 重点不是某一个瞬时数字，
# 而是观察随着测试持续运行，
# CPU或内存是否出现异常趋势。


import time
import psutil


# Linux下进程名称就是：
# DeviceServer
#
# 原计划附录中Windows示例是DeviceServer.exe，
# WSL/Linux必须改成DeviceServer。
PROCESS_NAME = "DeviceServer"


def find_process():
    """
    根据进程名称寻找DeviceServer。

    找到：
        返回psutil.Process对象

    没找到：
        返回None
    """

    # 遍历系统当前所有进程
    for process in psutil.process_iter(
        ["pid", "name"]
    ):

        # 判断名字是否正好是DeviceServer
        if process.info["name"] == PROCESS_NAME:
            return process

    return None


# 找到被测Server进程
process = find_process()


# 如果Server没有启动，
# 资源监控没有意义，所以直接退出。
if process is None:
    raise SystemExit(
        f"cannot find process: "
        f"{PROCESS_NAME}"
    )


print(
    "DeviceServer PID =",
    process.pid
)


print(
    "Start monitoring..."
)


# 第一轮先采20次。
#
# 每轮大约1秒：
# cpu_percent等待0.5秒
# + sleep等待0.5秒
#
# 所以大约观察20秒。180轮约等于3分钟，
for i in range(180):

    # cpu_percent：
    # 统计该进程CPU使用率
    cpu = process.cpu_percent(
        interval=0.5
    )


    # rss：
    # Resident Set Size
    #
    # 表示当前进程实际驻留在物理内存中的大小。
    #
    # 原始单位是字节，
    # /1024/1024转换成MB。
    mem_mb = (
        process.memory_info().rss
        / 1024
        / 1024
    )


    print(
        f"sample={i + 1:02d} "
        f"CPU={cpu:6.2f}% "
        f"RSS={mem_mb:8.2f} MB"
    )


    # 再等待0.5秒
    time.sleep(0.5)
