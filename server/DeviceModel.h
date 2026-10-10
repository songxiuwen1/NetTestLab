#pragma once

#include <mutex>
#include <chrono>
#include <string>


class DeviceModel
{
public:

    struct Snapshot
    {
        std::string state;

        int speed{};
        int duration{};
        int progress{};

        std::string result;
    };


    bool SetParam(
        int speed,
        int duration,
        std::string& error
    );

    bool StartTask(
        std::string& error
    );

    void StopTask();

    Snapshot GetSnapshot();


private:

    void UpdateLocked();


    std::mutex mutex_;

    std::string state_ = "IDLE";

    int speed_ = 1000;

    int duration_ = 3;

    int progress_ = 0;

    std::string result_ = "NONE";

    std::chrono::steady_clock::time_point
        startTime_{};
};
