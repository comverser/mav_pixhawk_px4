cmake_minimum_required(VERSION 3.10)
project(mavlink_px4_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# TODO: Add MAVLink library

# Main executable
add_executable(main
    src/main.cpp
    src/config.cpp
    src/mavlink/rc_telemetry.cpp
)

# TODO: Uncomment when MAVLink library is added
# target_link_libraries(main mavlink)

# TODO: MAVSDK implementation placeholder
