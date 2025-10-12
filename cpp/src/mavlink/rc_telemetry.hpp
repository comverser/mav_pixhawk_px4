#pragma once

#include <string>
#include <cstdint>
#include <sys/types.h>

namespace mavlink_impl {

class RCTelemetry {
public:
    RCTelemetry();
    ~RCTelemetry();

    void start();
    void stop();

private:
    void connect(const std::string& address);
    void connect_serial(const std::string& device, int baudrate);
    void monitor_rc_channels();

    int fd;
    bool connected;
};

} // namespace mavlink_impl
