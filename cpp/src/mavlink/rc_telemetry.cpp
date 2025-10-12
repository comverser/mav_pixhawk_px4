#include "rc_telemetry.hpp"
#include "../config.hpp"
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <common/mavlink.h>

namespace mavlink_impl {

RCTelemetry::RCTelemetry() : fd(-1), connected(false), is_serial(false) {
}

RCTelemetry::~RCTelemetry() {
    if (fd >= 0) {
        close(fd);
    }
}

void RCTelemetry::connect(const std::string& address) {
    // Parse serial connection (format: serial:/dev/ttyACM0:57600)
    if (address.find("serial:") == 0) {
        std::string addr_str = address.substr(7); // Remove "serial:"
        size_t colon_pos = addr_str.find(':');

        if (colon_pos == std::string::npos) {
            throw std::runtime_error("Invalid serial format. Expected serial:/dev/ttyXXX:baudrate");
        }

        std::string device = addr_str.substr(0, colon_pos);
        int baudrate = std::stoi(addr_str.substr(colon_pos + 1));

        connect_serial(device, baudrate);
        is_serial = true;
        return;
    }

    // Parse UDP address (format: udpin://0.0.0.0:14540)
    std::string addr_str = address;
    if (addr_str.find("udpin://") == 0) {
        addr_str = addr_str.substr(8);
    }

    size_t colon_pos = addr_str.find(':');
    if (colon_pos == std::string::npos) {
        throw std::runtime_error("Invalid UDP format. Expected udpin://host:port");
    }

    std::string ip = addr_str.substr(0, colon_pos);
    int port = std::stoi(addr_str.substr(colon_pos + 1));

    connect_udp(ip, port);
    is_serial = false;
}

void RCTelemetry::connect_udp(const std::string& ip, int port) {
    // Create UDP socket
    fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) {
        throw std::runtime_error("Failed to create socket");
    }

    // Bind to address
    sockaddr_in local_addr{};
    local_addr.sin_family = AF_INET;
    local_addr.sin_addr.s_addr = INADDR_ANY;
    local_addr.sin_port = htons(port);

    if (bind(fd, (sockaddr*)&local_addr, sizeof(local_addr)) < 0) {
        close(fd);
        throw std::runtime_error("Failed to bind socket");
    }

    std::cout << "Connected to " << ip << ":" << port << std::endl;
    connected = true;
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
    connected = true;
}

ssize_t RCTelemetry::read_data(uint8_t* buf, size_t len) {
    if (is_serial) {
        return read(fd, buf, len);
    } else {
        // Set timeout for UDP socket
        struct timeval tv;
        tv.tv_sec = 1;
        tv.tv_usec = 0;
        setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        return recv(fd, buf, len, 0);
    }
}

void RCTelemetry::monitor_rc_channels() {
    std::cout << "\n-- Monitoring RC Channels --" << std::endl;
    std::cout << "Ch1-4 typically: Roll, Pitch, Throttle, Yaw" << std::endl;
    std::cout << "Values range: 1000-2000 (1500 = center)\n" << std::endl;

    uint8_t buf[2048];
    mavlink_message_t msg;
    mavlink_status_t status;

    while (true) {
        ssize_t n = read_data(buf, sizeof(buf));
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

void RCTelemetry::start() {
    std::string address = config::get_connection_address();
    connect(address);
    monitor_rc_channels();
}

void RCTelemetry::stop() {
    connected = false;
    if (fd >= 0) {
        close(fd);
        fd = -1;
    }
    std::cout << "\nMonitoring complete" << std::endl;
}

} // namespace mavlink_impl
