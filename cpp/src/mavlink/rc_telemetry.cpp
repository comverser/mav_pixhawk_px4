#include "rc_telemetry.hpp"
#include "../config.hpp"
#include <common/mavlink.h>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <iostream>
#include <stdexcept>
#include <string>

namespace mavlink_impl {

// ============================================================================
// Constructor / Destructor
// ============================================================================

RCTelemetry::RCTelemetry() : fd(-1) {}

RCTelemetry::~RCTelemetry() {
    if (fd >= 0) {
        close(fd);
    }
}

// ============================================================================
// Connection
// ============================================================================

void RCTelemetry::connect(const std::string& address) {
    // Parse serial connection (format: serial:/dev/ttyACM0:57600)
    if (address.find("serial:") != 0) {
        throw std::runtime_error("Only serial connections are supported. Expected format: serial:/dev/ttyXXX:baudrate");
    }

    std::string addr_str = address.substr(7); // Remove "serial:"
    size_t colon_pos = addr_str.find(':');

    if (colon_pos == std::string::npos) {
        throw std::runtime_error("Invalid serial format. Expected serial:/dev/ttyXXX:baudrate");
    }

    std::string device = addr_str.substr(0, colon_pos);
    int baudrate = std::stoi(addr_str.substr(colon_pos + 1));

    connect_serial(device, baudrate);
}

void RCTelemetry::connect_serial(const std::string& device, int baudrate) {
    // Open serial device
    fd = open(device.c_str(), O_RDWR | O_NOCTTY);
    if (fd < 0) {
        throw std::runtime_error("Failed to open serial device: " + device);
    }

    // Configure serial port
    struct termios tty;
    if (tcgetattr(fd, &tty) != 0) {
        close(fd);
        throw std::runtime_error("Failed to get serial attributes");
    }

    // Set baud rate
    speed_t speed;
    switch (baudrate) {
        case 9600: speed = B9600; break;
        case 19200: speed = B19200; break;
        case 38400: speed = B38400; break;
        case 57600: speed = B57600; break;
        case 115200: speed = B115200; break;
        default:
            close(fd);
            throw std::runtime_error("Unsupported baud rate: " + std::to_string(baudrate));
    }

    cfsetospeed(&tty, speed);
    cfsetispeed(&tty, speed);

    // Configure port settings
    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;  // 8-bit chars
    tty.c_iflag &= ~IGNBRK;                       // disable break processing
    tty.c_lflag = 0;                              // no signaling chars, no echo, no canonical processing
    tty.c_oflag = 0;                              // no remapping, no delays
    tty.c_cc[VMIN]  = 0;                          // read doesn't block
    tty.c_cc[VTIME] = 10;                         // 1 second read timeout
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);       // shut off xon/xoff ctrl
    tty.c_cflag |= (CLOCAL | CREAD);              // ignore modem controls, enable reading
    tty.c_cflag &= ~(PARENB | PARODD);            // shut off parity
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;

    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        close(fd);
        throw std::runtime_error("Failed to set serial attributes");
    }

    std::cout << "Connected to " << device << " at " << baudrate << " baud" << std::endl;
}

// ============================================================================
// Monitoring
// ============================================================================

void RCTelemetry::monitor_rc_channels() {
    std::cout << "\n-- Monitoring RC Channels --" << std::endl;
    std::cout << "Ch1-4 typically: Roll, Pitch, Throttle, Yaw" << std::endl;
    std::cout << "Values range: 1000-2000 (1500 = center)\n" << std::endl;

    uint8_t buf[2048];
    mavlink_message_t msg;
    mavlink_status_t status;

    while (true) {
        ssize_t n = read(fd, buf, sizeof(buf));
        if (n > 0) {
            for (ssize_t i = 0; i < n; i++) {
                if (mavlink_parse_char(MAVLINK_COMM_0, buf[i], &msg, &status)) {
                    if (msg.msgid == MAVLINK_MSG_ID_RC_CHANNELS) {
                        mavlink_rc_channels_t rc;
                        mavlink_msg_rc_channels_decode(&msg, &rc);

                        std::cout << "CH1: " << rc.chan1_raw << " | "
                                  << "CH2: " << rc.chan2_raw << " | "
                                  << "CH3: " << rc.chan3_raw << " | "
                                  << "CH4: " << rc.chan4_raw << " | "
                                  << "CH5: " << rc.chan5_raw << " | "
                                  << "CH6: " << rc.chan6_raw << " | "
                                  << "CH7: " << rc.chan7_raw << " | "
                                  << "CH8: " << rc.chan8_raw << std::endl;
                    }
                }
            }
        }
    }
}

// ============================================================================
// Public Interface
// ============================================================================

void RCTelemetry::start() {
    std::string address = config::get_connection_address();
    connect(address);
    monitor_rc_channels();
}

} // namespace mavlink_impl
