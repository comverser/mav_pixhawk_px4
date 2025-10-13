#include "../config.hpp"
#include <mavsdk/mavsdk.h>
#include <iostream>
#include <future>
#include <chrono>

using namespace mavsdk;

int main() {
    std::string address = config::get_connection_address();

    Mavsdk mavsdk{Mavsdk::Configuration{ComponentType::GroundStation}};

    std::cout << "Checking heartbeat..." << std::endl;

    if (mavsdk.add_any_connection(address) != ConnectionResult::Success) {
        std::cerr << "✗ Connection failed" << std::endl;
        return 1;
    }

    auto prom = std::promise<void>{};
    auto fut = prom.get_future();

    mavsdk.subscribe_on_new_system([&]() {
        std::cout << "✓ Connected" << std::endl;
        prom.set_value();
    });

    if (fut.wait_for(std::chrono::seconds(5)) == std::future_status::timeout) {
        std::cerr << "✗ No heartbeat" << std::endl;
        return 1;
    }

    return 0;
}
