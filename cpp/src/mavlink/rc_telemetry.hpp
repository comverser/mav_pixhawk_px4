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
    void connect_udp(const std::string& ip, int port);
    void connect_serial(const std::string& device, int baudrate);
    void monitor_rc_channels();
    ssize_t read_data(uint8_t* buf, size_t len);

    int fd;
    bool connected;
    bool is_serial;
};

} // namespace mavlink_impl
