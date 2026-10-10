#pragma once

// 这个文件把 Windows Winsock 和 Linux POSIX Socket 的差异包起来。
// 这样同一套 Server.cpp 可以在 Windows 和 Linux 上复用。

#ifdef _WIN32

#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")

using SocketType = SOCKET;

inline bool InitSocketSystem()
{
    WSADATA wsaData{};
    return WSAStartup(MAKEWORD(2, 2), &wsaData) == 0;
}

inline void CleanupSocketSystem()
{
    WSACleanup();
}

inline void CloseSocket(SocketType s)
{
    closesocket(s);
}

inline int LastSocketError()
{
    return WSAGetLastError();
}

inline void SetRecvTimeout(SocketType s, int timeoutMs)
{
    DWORD timeout = static_cast<DWORD>(timeoutMs);

    setsockopt(
        s,
        SOL_SOCKET,
        SO_RCVTIMEO,
        reinterpret_cast<const char*>(&timeout),
        sizeof(timeout)
    );
}

#else

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cerrno>
#include <sys/time.h>
// Linux信号处理
// 用于忽略SIGPIPE，防止向已断开的Socket发送数据时
// 整个DeviceServer进程被操作系统直接终止
#include <csignal>


using SocketType = int;

constexpr SocketType INVALID_SOCKET = -1;
constexpr int SOCKET_ERROR = -1;


inline bool InitSocketSystem()
{
    // Linux中，如果对一个已经被对端关闭的TCP连接执行send，
    // 系统可能产生SIGPIPE信号。
    //
    // SIGPIPE默认行为可能直接终止整个进程。
    //
    // 测试场景中客户端可能主动超时、断线，
    // 服务器不能因为一个客户端异常就整个崩溃。
    //
    // 所以这里忽略SIGPIPE。
    //
    // 忽略以后：
    // send() 会返回失败，
    // 上层SendAll()可以正常检测错误并结束当前连接。
    std::signal(SIGPIPE, SIG_IGN);

    return true;
}


inline void CleanupSocketSystem()
{
}

inline void CloseSocket(SocketType s)
{
    close(s);
}

inline int LastSocketError()
{
    return errno;
}

inline void SetRecvTimeout(SocketType s, int timeoutMs)
{
    timeval tv{};

    tv.tv_sec = timeoutMs / 1000;
    tv.tv_usec = (timeoutMs % 1000) * 1000;

    setsockopt(
        s,
        SOL_SOCKET,
        SO_RCVTIMEO,
        &tv,
        sizeof(tv)
    );
}

#endif
