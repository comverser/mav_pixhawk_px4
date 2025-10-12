#include <iostream>
#include <string>
#include "mavlink/rc_telemetry.hpp"

void print_usage() {
    std::cout << "Usage: main <command>" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        print_usage();
        return 1;
    }

    std::string command = argv[1];

    try {
        if (command == "rc-monitor") {
            mavlink_impl::RCTelemetry rc_telem;
            rc_telem.start();
        } else {
            std::cerr << "Unknown command: " << command << std::endl;
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}

// TODO: MAVSDK implementation placeholder
