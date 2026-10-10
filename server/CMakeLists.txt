cmake_minimum_required(VERSION 3.16)


project(
    DeviceServer
    LANGUAGES CXX
)


set(
    CMAKE_CXX_STANDARD
    17
)


set(
    CMAKE_CXX_STANDARD_REQUIRED
    ON
)


add_executable(
    DeviceServer

    main.cpp
    Protocol.cpp
    DeviceModel.cpp
    Server.cpp
)


target_include_directories(
    DeviceServer
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)


find_package(
    Threads
    REQUIRED
)


target_link_libraries(
    DeviceServer
    PRIVATE
    Threads::Threads
)


if (WIN32)

    target_link_libraries(
        DeviceServer
        PRIVATE
        ws2_32
    )

endif()
