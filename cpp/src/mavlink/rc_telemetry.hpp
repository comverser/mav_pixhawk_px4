#pragma once

#include <string>

namespace mavlink_impl {

/**
 * RC telemetry monitor for serial connections
 * Monitors RC_CHANNELS messages from MAVLink stream
 */
class RCTelemetry {
public:
    RCTelemetry();
    ~RCTelemetry();

    // Start monitoring (blocks until Ctrl+C)
    void start();

private:
    // Connection
    void connect(const std::string& address);
    void connect_serial(const std::string& device, int baudrate);

    // Monitoring
    void monitor_rc_channels();

    // State
    int fd;
};

} // namespace mavlink_impl
