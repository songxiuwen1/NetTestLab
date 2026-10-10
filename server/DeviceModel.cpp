#include "DeviceModel.h"

#include <algorithm>


bool DeviceModel::SetParam(
    int speed,
    int duration,
    std::string& error
)
{
    std::lock_guard<std::mutex> lock(mutex_);


    if (speed < 0 || speed > 5000)
    {
        error =
            "speed must be in [0, 5000]";

        return false;
    }


    if (duration < 1 || duration > 60)
    {
        error =
            "duration must be in [1, 60]";

        return false;
    }


    if (state_ == "RUNNING")
    {
        error =
            "cannot change parameter while running";

        return false;
    }


    speed_ = speed;
    duration_ = duration;

    return true;
}


bool DeviceModel::StartTask(
    std::string& error
)
{
    std::lock_guard<std::mutex> lock(mutex_);

    UpdateLocked();


    if (state_ == "RUNNING")
    {
        error =
            "task already running";

        return false;
    }


    state_ = "RUNNING";
    progress_ = 0;
    result_ = "NONE";

    startTime_ =
        std::chrono::steady_clock::now();

    return true;
}


void DeviceModel::StopTask()
{
    std::lock_guard<std::mutex> lock(mutex_);

    state_ = "IDLE";
    progress_ = 0;
    result_ = "STOPPED";
}


void DeviceModel::UpdateLocked()
{
    if (state_ != "RUNNING")
        return;


    const auto now =
        std::chrono::steady_clock::now();


    const double elapsed =
        std::chrono::duration<double>(
            now - startTime_
        ).count();


    progress_ =
        static_cast<int>(
            elapsed / duration_ * 100.0
        );


    progress_ =
        std::clamp(
            progress_,
            0,
            100
        );


    if (elapsed >= duration_)
    {
        state_ = "FINISHED";
        progress_ = 100;
        result_ = "OK";
    }
}


DeviceModel::Snapshot
DeviceModel::GetSnapshot()
{
    std::lock_guard<std::mutex> lock(mutex_);

    UpdateLocked();

    return {
        state_,
        speed_,
        duration_,
        progress_,
        result_
    };
}
