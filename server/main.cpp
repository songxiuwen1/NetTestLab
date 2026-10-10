#include "Server.h"
#include "SocketCompat.h"

#include <iostream>


int main()
{
    // Windows需要初始化Winsock；
    // Linux这里什么都不用做，会直接返回true。
    if (!InitSocketSystem())
    {
        std::cerr
            << "Socket system init failed.\n";

        return 1;
    }


    // 创建一个拥有4个Worker线程的服务端
    DeviceServer server(4);


    // 启动TCP 9000端口
    if (!server.Start(9000))
    {
        CleanupSocketSystem();

        return 2;
    }


    // 一直等待并处理客户端
    server.Run();


    CleanupSocketSystem();

    return 0;
}
