#pragma once

#include "SocketCompat.h"
#include "DeviceModel.h"
#include "ThreadPool.h"

#include <atomic>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>


class DeviceServer
{
public:

    explicit DeviceServer(
        std::size_t workerCount = 4
    );

    ~DeviceServer();


    bool Start(
        std::uint16_t port
    );

    void Run();


private:

    void HandleClient(
        SocketType client
    );


    std::string ProcessCommand(
        std::uint8_t command,
        const std::string& payload
    );


    void Log(
        const std::string& text
    );


    SocketType listenSocket_ =
        INVALID_SOCKET;


    std::unique_ptr<ThreadPool>
        pool_;


    DeviceModel
        device_;


    std::atomic<std::uint64_t>
        totalRequests_{0};


    std::atomic<std::uint64_t>
        successRequests_{0};


    std::mutex
        logMutex_;


    std::size_t
        workerCount_ = 4;
};
