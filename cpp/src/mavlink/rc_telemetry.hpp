#pragma once

// TODO: Include MAVLink headers

namespace mavlink_impl {

class RCTelemetry {
public:
    RCTelemetry();
    ~RCTelemetry();

    void start();
    void stop();

private:
    // TODO: Add connection and message handling
};

} // namespace mavlink_impl
