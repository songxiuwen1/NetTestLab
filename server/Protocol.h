#pragma once

#include "SocketCompat.h"

#include <cstdint>
#include <string>

namespace proto
{

constexpr std::uint16_t MAGIC = 0xAA55;
constexpr std::uint8_t VERSION = 1;

// 最大 1 MB，防止恶意或异常 Length 让程序申请巨量内存
constexpr std::uint32_t MAX_PAYLOAD = 1024 * 1024;


// 我们自己定义的应用层命令
enum class Command : std::uint8_t
{
    GET_STATUS    = 0x01,
    SET_PARAM     = 0x02,
    START_TASK    = 0x03,
    STOP_TASK     = 0x04,
    GET_RESULT    = 0x05,
    HEARTBEAT     = 0x06,
    SLOW_RESPONSE = 0x07
};


#pragma pack(push, 1)

// 固定 12 字节协议头
// 2 + 1 + 1 + 4 + 4 = 12
struct PacketHeader
{
    std::uint16_t magic;
    std::uint8_t version;
    std::uint8_t command;
    std::uint32_t sequence;
    std::uint32_t length;
};

#pragma pack(pop)


struct Packet
{
    Command command{};
    std::uint32_t sequence{};
    std::string payload;
};


bool RecvExact(
    SocketType s,
    void* buffer,
    std::size_t size
);

bool SendAll(
    SocketType s,
    const void* buffer,
    std::size_t size
);

bool RecvPacket(
    SocketType s,
    Packet& packet,
    std::string& error
);

bool SendPacket(
    SocketType s,
    Command command,
    std::uint32_t sequence,
    const std::string& payload
);

}
