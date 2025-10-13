cmake_minimum_required(VERSION 3.10)
project(mavlink_px4_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# Dependencies
# ============================================================================

# MAVLink headers (header-only library)
set(MAVLINK_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/external/mavlink")

# ============================================================================
# Common Sources
# ============================================================================

set(COMMON_SOURCES
    src/config.cpp
)

# ============================================================================
# MAVLink Implementation
# ============================================================================

add_executable(main
    src/main.cpp
    src/mavlink/rc_telemetry.cpp
    ${COMMON_SOURCES}
)

target_include_directories(main PRIVATE ${MAVLINK_INCLUDE_DIR})

# ============================================================================
# MAVSDK Implementation
# ============================================================================

add_executable(heartbeat_monitor
    src/mavsdk/heartbeat_monitor.cpp
    ${COMMON_SOURCES}
)

target_link_libraries(heartbeat_monitor PRIVATE mavsdk)
