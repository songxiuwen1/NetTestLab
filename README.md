# NetTestLab

Linux C++ 网络服务自动化测试平台。

本项目用于练习和验证 Linux 环境下 C++ 网络服务的软件测试流程，
包含自定义 TCP 二进制协议、Python/pytest 自动化测试、
Shell 一键回归、并发与稳定性测试、日志分析、GDB/Valgrind 调试
以及 tcpdump/Wireshark 网络抓包分析。

---

## 1. 项目背景

项目被测对象为自研的 C++ DeviceServer。

DeviceServer 模拟一个简单设备服务，通过 TCP 9000 端口接收客户端请求，
解析自定义二进制协议，并完成状态查询、参数设置、任务启动、
任务停止和心跳等操作。

Python 测试端通过 pytest 对服务端进行功能、边界、异常、
协议、超时、断线、并发和稳定性验证。

项目主要用于练习以下软件测试能力：

- Linux 环境下的软件测试与问题定位
- Python/pytest 自动化测试
- TCP Socket 与自定义二进制协议测试
- 功能、边界、异常、并发和稳定性测试
- Shell 自动化回归
- 日志、GDB、Valgrind、tcpdump 和 Wireshark 问题分析

---

## 2. 系统架构

```text
Python / pytest 测试端
        |
        | TCP
        | 自定义二进制协议
        v
+---------------------------+
|     C++ DeviceServer      |
|                           |
| TCP Socket                |
| Protocol Parser           |
| Thread Pool               |
| Device State Machine      |
+---------------------------+
        |
        v
    DeviceModel
