#include "Server.h"
#include "Protocol.h"

#include <algorithm>
#include <chrono>
#include <iostream>
#include <map>
#include <sstream>
#include <thread>


namespace
{

std::map<std::string, std::string>
ParseKV(const std::string& text)
{
    std::map<std::string, std::string> out;

    std::stringstream ss(text);

    std::string item;


    while (std::getline(ss, item, ';'))
    {
        auto pos = item.find('=');

        if (pos != std::string::npos)
        {
            out[item.substr(0, pos)] =
                item.substr(pos + 1);
        }
    }

    return out;
}


int ToInt(
    const std::map<std::string, std::string>& kv,
    const std::string& key,
    int defaultValue
)
{
    auto it = kv.find(key);

    if (it == kv.end())
        return defaultValue;


    try
    {
        return std::stoi(it->second);
    }
    catch (...)
    {
        return defaultValue;
    }
}

}


DeviceServer::DeviceServer(
    std::size_t workerCount
)
    : workerCount_(workerCount)
{
}


DeviceServer::~DeviceServer()
{
    pool_.reset();

    if (
        listenSocket_
        != INVALID_SOCKET
    )
    {
        CloseSocket(
            listenSocket_
        );
    }
}


bool DeviceServer::Start(
    std::uint16_t port
)
{
    // 创建 TCP Socket
    listenSocket_ =
        socket(
            AF_INET,
            SOCK_STREAM,
            IPPROTO_TCP
        );


    if (
        listenSocket_
        == INVALID_SOCKET
    )
    {
        Log("socket() failed");
        return false;
    }


    int opt = 1;

    setsockopt(
        listenSocket_,
        SOL_SOCKET,
        SO_REUSEADDR,
        reinterpret_cast<const char*>(&opt),
        sizeof(opt)
    );


    sockaddr_in addr{};

    addr.sin_family =
        AF_INET;

    addr.sin_addr.s_addr =
        htonl(INADDR_ANY);

    addr.sin_port =
        htons(port);


    // bind：绑定到指定端口
    if (
        bind(
            listenSocket_,
            reinterpret_cast<sockaddr*>(&addr),
            sizeof(addr)
        )
        == SOCKET_ERROR
    )
    {
        Log(
            "bind() failed, error="
            + std::to_string(
                LastSocketError()
            )
        );

        return false;
    }


    // listen：开始监听
    if (
        listen(
            listenSocket_,
            16
        )
        == SOCKET_ERROR
    )
    {
        Log("listen() failed");
        return false;
    }


    pool_ =
        std::make_unique<ThreadPool>(
            workerCount_,
            [this](SocketType client)
            {
                HandleClient(client);
            }
        );


    Log(
        "Server started, port="
        + std::to_string(port)
        + ", workers="
        + std::to_string(workerCount_)
    );


    return true;
}


void DeviceServer::Run()
{
    Log(
        "Waiting for clients... Press Ctrl+C to stop."
    );


    while (true)
    {
        sockaddr_in clientAddr{};


#ifdef _WIN32

        int len =
            sizeof(clientAddr);

#else

        socklen_t len =
            sizeof(clientAddr);

#endif


        // accept：等待客户端连接
        SocketType client =
            accept(
                listenSocket_,
                reinterpret_cast<sockaddr*>(
                    &clientAddr
                ),
                &len
            );


        if (
            client == INVALID_SOCKET
        )
        {
            Log("accept() failed");
            continue;
        }


        // 把客户端交给线程池，
        // accept 主线程继续等待其他客户端。
        pool_->Enqueue(client);
    }
}


void DeviceServer::HandleClient(
    SocketType client
)
{
    // 3 秒接收超时
    SetRecvTimeout(
        client,
        3000
    );


    while (true)
    {
        proto::Packet packet;

        std::string error;


        if (
            !proto::RecvPacket(
                client,
                packet,
                error
            )
        )
        {
            // 正常断开、半包、非法Magic等
            // 都应该可控结束，而不是让服务器崩溃。
            if (
                error
                !=
                "connection closed / timeout while receiving header"
            )
            {
                Log(
                    "RecvPacket stopped: "
                    + error
                );
            }

            break;
        }


        totalRequests_.fetch_add(1);


        const std::string reply =
            ProcessCommand(
                static_cast<std::uint8_t>(
                    packet.command
                ),
                packet.payload
            );


        if (
            reply.rfind(
                "code=0",
                0
            )
            == 0
        )
        {
            successRequests_.fetch_add(1);
        }


        if (
            !proto::SendPacket(
                client,
                packet.command,
                packet.sequence,
                reply
            )
        )
        {
            break;
        }
    }


    CloseSocket(client);
}


std::string
DeviceServer::ProcessCommand(
    std::uint8_t command,
    const std::string& payload
)
{
    using proto::Command;


    auto cmd =
        static_cast<Command>(
            command
        );


    if (cmd == Command::HEARTBEAT)
    {
        return
            "code=0;message=PONG";
    }


    if (
        cmd == Command::GET_STATUS
        ||
        cmd == Command::GET_RESULT
    )
    {
        auto s =
            device_.GetSnapshot();


        std::ostringstream os;


        os
            << "code=0"

            << ";state="
            << s.state

            << ";speed="
            << s.speed

            << ";duration="
            << s.duration

            << ";progress="
            << s.progress

            << ";result="
            << s.result

            << ";total_requests="
            << totalRequests_.load()

            << ";success_requests="
            << successRequests_.load();


        return os.str();
    }


    if (cmd == Command::SET_PARAM)
    {
        auto kv =
            ParseKV(payload);


        int speed =
            ToInt(
                kv,
                "speed",
                -99999
            );


        int duration =
            ToInt(
                kv,
                "duration",
                -99999
            );


        std::string error;


        if (
            !device_.SetParam(
                speed,
                duration,
                error
            )
        )
        {
            return
                "code=422;message="
                + error;
        }


        return
            "code=0;message=PARAM_OK";
    }


    if (cmd == Command::START_TASK)
    {
        std::string error;


        if (
            !device_.StartTask(
                error
            )
        )
        {
            return
                "code=409;message="
                + error;
        }


        return
            "code=0;message=STARTED";
    }


    if (cmd == Command::STOP_TASK)
    {
        device_.StopTask();

        return
            "code=0;message=STOPPED";
    }


    if (cmd == Command::SLOW_RESPONSE)
    {
        auto kv =
            ParseKV(payload);


        int ms =
            ToInt(
                kv,
                "ms",
                1000
            );


        ms =
            std::max(
                0,
                std::min(
                    ms,
                    5000
                )
            );


        std::this_thread::sleep_for(
            std::chrono::milliseconds(ms)
        );


        return
            "code=0;message=SLOW_DONE";
    }


    return
        "code=400;message=UNKNOWN_COMMAND";
}


void DeviceServer::Log(
    const std::string& text
)
{
    std::lock_guard<std::mutex>
        lock(logMutex_);


    std::cout
        << "[SERVER] "
        << text
        << std::endl;
}
