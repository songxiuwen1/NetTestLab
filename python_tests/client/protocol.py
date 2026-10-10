# protocol.py
# 作用：
# Python 客户端必须使用和 C++ 服务端完全一样的二进制协议。
# 如果字段顺序、长度或字节序不同，双方就无法正确通信。

import socket
import struct


# 协议固定 Magic。
# C++ 端对应：constexpr std::uint16_t MAGIC = 0xAA55;
MAGIC = 0xAA55


# 当前协议版本。
# C++ 端对应：constexpr std::uint8_t VERSION = 1;
VERSION = 1


# Python struct 格式：
# !  = 使用网络字节序，也就是大端
# H  = unsigned short，2字节，对应 Magic
# B  = unsigned char，1字节，对应 Version
# B  = unsigned char，1字节，对应 Command
# I  = unsigned int，4字节，对应 Sequence
# I  = unsigned int，4字节，对应 Length
#
# 总长度：
# 2 + 1 + 1 + 4 + 4 = 12 字节
HEADER_FMT = "!HBBII"


# 自动计算协议头大小。
# 按当前格式应该得到12。
HEADER_SIZE = struct.calcsize(
    HEADER_FMT
)


# 以下命令值必须和 C++ Command 枚举完全一致。

# 查询状态
GET_STATUS = 0x01

# 设置参数
SET_PARAM = 0x02

# 开始任务
START_TASK = 0x03

# 停止任务
STOP_TASK = 0x04

# 获取结果
GET_RESULT = 0x05

# 心跳
HEARTBEAT = 0x06

# 故意慢响应，用于后续超时测试
SLOW_RESPONSE = 0x07


def pack_packet(
    command: int,
    sequence: int,
    payload: str = ""
) -> bytes:
    """
    把 Command、Sequence 和 Payload
    打包成可以通过 TCP 发送的二进制协议包。
    """

    # Python字符串不能直接作为二进制协议 Payload，
    # 所以先编码成 UTF-8 bytes。
    body = payload.encode("utf-8")


    # 按 HEADER_FMT 构造固定12字节协议头。
    #
    # HEADER_FMT 中的 ! 已经指定网络字节序，
    # 所以 Python 不需要再手动调用 htonl。
    header = struct.pack(
        HEADER_FMT,

        MAGIC,          # 2字节
        VERSION,        # 1字节
        command,        # 1字节
        sequence,       # 4字节
        len(body),      # 4字节：Payload实际长度
    )


    # 完整协议包：
    # 12字节Header + Payload
    return header + body


def recv_exact(
    sock: socket.socket,
    n: int
) -> bytes:
    """
    精确接收 n 字节。

    TCP没有消息边界，
    所以一次 recv(n) 不保证真的返回n字节。
    必须循环读取直到收满。
    """

    # 用列表暂存每一次收到的字节块
    chunks = []

    # 当前累计收到多少字节
    received = 0


    # 只要还没达到目标长度，就继续接收
    while received < n:

        # 本次只请求还缺少的字节数
        chunk = sock.recv(
            n - received
        )


        # 如果返回空bytes，
        # 通常说明对端已经关闭连接
        if not chunk:
            raise ConnectionError(
                "socket closed before enough bytes arrived"
            )


        # 保存本次数据
        chunks.append(chunk)

        # 更新累计字节数
        received += len(chunk)


    # 把多个字节块拼成完整bytes
    return b"".join(chunks)


def recv_packet(
    sock: socket.socket
):
    """
    从TCP字节流中恢复一条完整协议消息。
    """

    # 第一步：
    # 永远先收固定的12字节Header
    header = recv_exact(
        sock,
        HEADER_SIZE
    )


    # 第二步：
    # 按和发送端相同的格式解析Header
    magic, version, command, sequence, length = (
        struct.unpack(
            HEADER_FMT,
            header
        )
    )


    # 检查协议Magic
    if magic != MAGIC:
        raise ValueError(
            f"bad magic: 0x{magic:04X}"
        )


    # 检查协议版本
    if version != VERSION:
        raise ValueError(
            f"bad version: {version}"
        )


    # 第三步：
    # 根据Length决定后面还要收多少Payload。
    #
    # Length=0时说明没有Payload。
    if length:
        payload = recv_exact(
            sock,
            length
        ).decode("utf-8")
    else:
        payload = ""


    # 返回解析后的协议字段
    return command, sequence, payload



def parse_kv(text: str) -> dict:
    """
    把服务端返回的 key=value;key=value 字符串
    转换成 Python 字典。

    例如：
    code=0;message=PONG

    转换为：
    {
        "code": "0",
        "message": "PONG"
    }
    """

    # 创建空字典，用于保存解析结果
    result = {}


    # 服务端不同字段之间使用分号 ; 分隔
    #
    # 例如：
    # code=0;message=PONG
    #
    # split(";") 后得到：
    # ["code=0", "message=PONG"]
    for item in text.split(";"):

        # 只有包含 = 的内容才认为是合法 key=value
        if "=" in item:

            # 只按照第一个 = 进行切分
            #
            # 例如：
            # "code=0"
            #
            # 得到：
            # key   = "code"
            # value = "0"
            key, value = item.split("=", 1)

            # 保存到字典中
            result[key] = value


    # 返回解析完成的字典
    return result
