#include "Protocol.h"

#include <vector>
#include <cstring>


namespace proto
{

bool RecvExact(
    SocketType s,
    void* buffer,
    std::size_t size
)
{
    auto* out = static_cast<char*>(buffer);

    std::size_t received = 0;

    // TCP 是字节流。
    // 一次 recv 不保证得到想要的全部数据，
    // 所以循环读取直到拿满 size 字节。
    while (received < size)
    {
        int n = recv(
            s,
            out + received,
            static_cast<int>(size - received),
            0
        );

        if (n <= 0)
            return false;

        received += static_cast<std::size_t>(n);
    }

    return true;
}


bool SendAll(
    SocketType s,
    const void* buffer,
    std::size_t size
)
{
    const auto* in =
        static_cast<const char*>(buffer);

    std::size_t sent = 0;

    while (sent < size)
    {
        int n = send(
            s,
            in + sent,
            static_cast<int>(size - sent),
            0
        );

        if (n <= 0)
            return false;

        sent += static_cast<std::size_t>(n);
    }

    return true;
}


bool RecvPacket(
    SocketType s,
    Packet& packet,
    std::string& error
)
{
    PacketHeader netHeader{};

    if (!RecvExact(
            s,
            &netHeader,
            sizeof(netHeader)))
    {
        error =
            "connection closed / timeout while receiving header";

        return false;
    }


    // 网络中的多字节整数统一使用网络字节序，
    // 收到后转换回当前机器的主机字节序。
    const std::uint16_t magic =
        ntohs(netHeader.magic);

    const std::uint32_t seq =
        ntohl(netHeader.sequence);

    const std::uint32_t len =
        ntohl(netHeader.length);


    if (magic != MAGIC)
    {
        error = "invalid magic";
        return false;
    }

    if (netHeader.version != VERSION)
    {
        error = "unsupported version";
        return false;
    }

    if (len > MAX_PAYLOAD)
    {
        error = "payload too large";
        return false;
    }


    packet.command =
        static_cast<Command>(netHeader.command);

    packet.sequence = seq;

    packet.payload.clear();


    if (len > 0)
    {
        packet.payload.resize(len);

        if (!RecvExact(
                s,
                packet.payload.data(),
                len))
        {
            error =
                "connection closed / timeout while receiving payload";

            return false;
        }
    }

    return true;
}


bool SendPacket(
    SocketType s,
    Command command,
    std::uint32_t sequence,
    const std::string& payload
)
{
    PacketHeader header{};

    header.magic =
        htons(MAGIC);

    header.version =
        VERSION;

    header.command =
        static_cast<std::uint8_t>(command);

    header.sequence =
        htonl(sequence);

    header.length =
        htonl(
            static_cast<std::uint32_t>(
                payload.size()
            )
        );


    if (!SendAll(
            s,
            &header,
            sizeof(header)))
    {
        return false;
    }


    if (!payload.empty()
        && !SendAll(
            s,
            payload.data(),
            payload.size()))
    {
        return false;
    }

    return true;
}

}
