cmake_minimum_required(VERSION 3.10)
project(mavlink_px4_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# MAVLink headers (header-only library)
set(MAVLINK_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/external/mavlink")

# Main executable
add_executable(main
    src/main.cpp
    src/config.cpp
    src/mavlink/rc_telemetry.cpp
)

target_include_directories(main PRIVATE ${MAVLINK_INCLUDE_DIR})

# TODO: MAVSDK implementation placeholder
