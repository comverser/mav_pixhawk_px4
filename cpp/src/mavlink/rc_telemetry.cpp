#include "rc_telemetry.hpp"
#include <iostream>

namespace mavlink_impl {

RCTelemetry::RCTelemetry() {
    // TODO: Initialize MAVLink connection
}

RCTelemetry::~RCTelemetry() {
    // TODO: Cleanup
}

void RCTelemetry::start() {
    std::cout << "MAVLink RC Telemetry: Starting..." << std::endl;
    // TODO: Subscribe to RC_CHANNELS messages
    // TODO: Process and display RC data
}

void RCTelemetry::stop() {
    std::cout << "MAVLink RC Telemetry: Stopping..." << std::endl;
    // TODO: Stop telemetry
}

} // namespace mavlink_impl
