#include "config.hpp"
#include <cstdlib>
#include <stdexcept>

namespace config {

std::string get_connection_address() {
    const char* address = std::getenv("DRONE_ADDRESS");
    if (!address) {
        throw std::runtime_error("DRONE_ADDRESS environment variable not set");
    }
    return std::string(address);
}

} // namespace config
