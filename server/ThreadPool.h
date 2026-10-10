#pragma once

#include "SocketCompat.h"

#include <atomic>
#include <condition_variable>
#include <functional>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>


// 线程池的任务：处理已经 accept 的客户端 Socket。
// 主线程相当于 Producer；
// Worker 线程相当于 Consumer。

class ThreadPool
{
public:

    ThreadPool(
        std::size_t workerCount,
        std::function<void(SocketType)> handler
    )
        : handler_(std::move(handler))
    {
        for (
            std::size_t i = 0;
            i < workerCount;
            ++i
        )
        {
            workers_.emplace_back(
                [this]()
                {
                    WorkerLoop();
                }
            );
        }
    }


    ~ThreadPool()
    {
        {
            std::lock_guard<std::mutex>
                lock(mutex_);

            stopping_ = true;
        }

        cv_.notify_all();


        for (auto& t : workers_)
        {
            if (t.joinable())
                t.join();
        }
    }


    void Enqueue(SocketType client)
    {
        {
            std::lock_guard<std::mutex>
                lock(mutex_);

            queue_.push(client);
        }

        // 新任务到达，只唤醒一个 Worker
        cv_.notify_one();
    }


private:

    void WorkerLoop()
    {
        while (true)
        {
            SocketType client =
                INVALID_SOCKET;


            {
                std::unique_lock<std::mutex>
                    lock(mutex_);


                // 队列没任务时线程睡眠，
                // 避免不停循环白白占用 CPU。
                cv_.wait(
                    lock,
                    [this]()
                    {
                        return stopping_
                            || !queue_.empty();
                    }
                );


                if (
                    stopping_
                    && queue_.empty()
                )
                {
                    return;
                }


                client =
                    queue_.front();

                queue_.pop();
            }


            handler_(client);
        }
    }


    std::vector<std::thread>
        workers_;

    std::queue<SocketType>
        queue_;

    std::mutex
        mutex_;

    std::condition_variable
        cv_;

    bool
        stopping_ = false;

    std::function<void(SocketType)>
        handler_;
};
