# ============================================================================
# Configuration
# ============================================================================

# Default device paths and baud rates
USB_PORT := "/dev/ttyACM0"
UART_PORT := "/dev/ttyAMA0"
USB_BAUD := "57600"
UART_BAUD := "921600"
DEFAULT_DURATION := "10"
QGC_PORT := "14550"
QGC_HOST := "211.60.101.110"
QGC_VIDEO_PORT := "5600"
CAMERA_URL := "rtsp://192.168.144.25:8554/main.264"
LTE_IFACE := "wwan0"

# ============================================================================
# Quick Start
# ============================================================================

default: menu

# Interactive menu to select language and run examples
menu: setup
    @just _menu

# Interactive run (alias for menu)
run: menu

# ============================================================================
# Setup & Cleanup
# ============================================================================

# Pull latest changes and update submodules
setup:
    git pull --rebase --autostash
    git submodule update --init --remote

# Clean all build artifacts (Python, C++, Rust)
clean: python-clean cpp-clean rust-clean

# ============================================================================
# Python
# ============================================================================

# Setup Python virtual environment and dependencies
python-setup:
    @test -d python/venv || python3 -m venv python/venv
    @python/venv/bin/pip install -q -r python/requirements.txt

# Run Python examples interactively
python-run: python-setup
    @just _python-interactive

# Clean Python artifacts
python-clean:
    @rm -rf python/venv
    @find python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @find python -type f -name "*.pyc" -delete 2>/dev/null || true
    @find python -type f -name "*.pyo" -delete 2>/dev/null || true

# ============================================================================
# C++
# ============================================================================

# Setup C++ dependencies (MAVSDK)
cpp-setup:
    #!/usr/bin/env bash
    # Check if MAVSDK is already installed
    if ldconfig -p | grep -q libmavsdk.so; then
        echo "✓ MAVSDK already installed"
        exit 0
    fi

    echo "Installing MAVSDK..."

    # Install MAVSDK system dependencies
    sudo apt-get update
    sudo apt-get install -y \
        libcurl4-openssl-dev \  # MAVSDK: HTTP/HTTPS communication
        libjsoncpp-dev \         # MAVSDK: JSON parsing
        libtinyxml2-dev          # MAVSDK: XML parsing (component metadata)

    # Build and install MAVSDK from submodule
    cd cpp/external/mavsdk
    cmake -Bbuild -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON
    sudo cmake --build build --target install -j$(nproc)

    # Update library cache
    sudo ldconfig
    echo "✓ MAVSDK installed successfully"

# Build C++ project
cpp-build: cpp-setup
    @mkdir -p cpp/build
    @cd cpp/build && cmake .. && make

# Run C++ examples interactively
cpp-run: cpp-build
    @just _cpp-interactive

# Clean C++ build artifacts
cpp-clean:
    @rm -rf cpp/build

# ============================================================================
# Rust
# ============================================================================

# Build Rust project
rust-build:
    @cd rust && cargo build --release

# Run Rust examples interactively
rust-run: rust-build
    @just _rust-interactive

# Clean Rust build artifacts
rust-clean:
    @test -d rust/target && cd rust && cargo clean || true

# ============================================================================
# LTE Route Pinning
# ============================================================================

# Install helper script to pin host traffic to LTE interface
_lte-route-install:
    #!/usr/bin/env bash
    sudo tee /usr/local/bin/ensure-lte-route > /dev/null <<'SCRIPT'
    #!/bin/sh
    HOST="$1"
    IFACE="$2"
    GW=$(ip route show default dev "$IFACE" 2>/dev/null | head -1 | cut -d' ' -f3)
    if [ -n "$GW" ]; then
        ip route replace "$HOST/32" via "$GW" dev "$IFACE"
    else
        echo "Warning: no default gateway found on $IFACE" >&2
        exit 1
    fi
    SCRIPT
    sudo chmod +x /usr/local/bin/ensure-lte-route

# ============================================================================
# MAVLink Router (forward TELEM2 to remote QGroundControl)
# ============================================================================

# Install mavlink-router from source
router-install:
    #!/usr/bin/env bash
    if command -v mavlink-routerd &> /dev/null; then
        echo "mavlink-router already installed: $(mavlink-routerd --version 2>&1 || echo 'ok')"
        exit 0
    fi
    sudo apt-get update && sudo apt-get install -y git meson ninja-build pkg-config gcc g++ python3 libsystemd-dev
    tmpdir=$(mktemp -d)
    git clone https://github.com/mavlink-router/mavlink-router.git "$tmpdir"
    cd "$tmpdir"
    git submodule update --init --recursive
    meson setup build . -Dsystemdsystemunitdir=/usr/lib/systemd/system
    ninja -C build
    sudo ninja -C build install
    rm -rf "$tmpdir"
    echo "mavlink-router installed successfully"

# Start forwarding TELEM2 to remote QGC
router-start: _lte-route-install
    #!/usr/bin/env bash
    sudo mkdir -p /etc/mavlink-router
    sudo tee /etc/mavlink-router/main.conf > /dev/null <<CONF
    [General]
    TcpServerPort = 0
    ReportStats = false

    [UartEndpoint telem2]
    Device = {{UART_PORT}}
    Baud = {{UART_BAUD}}

    [UdpEndpoint qgc]
    Mode = Normal
    Address = {{QGC_HOST}}
    Port = {{QGC_PORT}}
    CONF
    # Create systemd drop-in: wait for network, pin to LTE, slow restart
    sudo mkdir -p /etc/systemd/system/mavlink-router.service.d
    sudo tee /etc/systemd/system/mavlink-router.service.d/override.conf > /dev/null <<DROPIN
    [Unit]
    After=network-online.target
    Wants=network-online.target

    [Service]
    ExecStartPre=+/usr/local/bin/ensure-lte-route {{QGC_HOST}} {{LTE_IFACE}}
    RestartSec=5
    DROPIN
    sudo systemctl daemon-reload
    sudo systemctl enable mavlink-router
    sudo systemctl restart mavlink-router
    echo "Forwarding {{UART_PORT}} @ {{UART_BAUD}} -> {{QGC_HOST}}:{{QGC_PORT}}"
    sudo systemctl status mavlink-router --no-pager

# Stop mavlink-router
router-stop:
    sudo systemctl stop mavlink-router

# Show mavlink-router status
router-status:
    sudo systemctl status mavlink-router --no-pager

# Enable mavlink-router on boot
router-enable: router-start

# Disable mavlink-router on boot
router-disable:
    sudo systemctl disable mavlink-router
    sudo systemctl stop mavlink-router
    echo "mavlink-router disabled and stopped"

# Show mavlink-router logs
router-log:
    sudo journalctl -u mavlink-router -f

# ============================================================================
# Video Stream (forward camera RTSP to remote QGroundControl via UDP)
# ============================================================================

# Start forwarding camera stream to remote QGC
stream-start: _lte-route-install
    #!/usr/bin/env bash
    sudo tee /etc/systemd/system/video-stream.service > /dev/null <<EOF
    [Unit]
    Description=Video stream relay to QGC
    After=network-online.target
    Wants=network-online.target

    [Service]
    ExecStartPre=+/usr/local/bin/ensure-lte-route {{QGC_HOST}} {{LTE_IFACE}}
    ExecStart=/usr/bin/ffmpeg -rtsp_transport tcp -timeout 5000000 -fflags +genpts+discardcorrupt -i {{CAMERA_URL}} -c:v copy -bsf:v dump_extra -an -f mpegts -mpegts_flags +resend_headers udp://{{QGC_HOST}}:{{QGC_VIDEO_PORT}}?pkt_size=1316
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    EOF
    sudo systemctl daemon-reload
    sudo systemctl enable video-stream
    sudo systemctl restart video-stream
    echo "Streaming {{CAMERA_URL}} -> {{QGC_HOST}}:{{QGC_VIDEO_PORT}}"
    sudo systemctl status video-stream --no-pager

# Stop video stream
stream-stop:
    sudo systemctl stop video-stream

# Show video stream status
stream-status:
    sudo systemctl status video-stream --no-pager

# Disable video stream on boot
stream-disable:
    sudo systemctl disable video-stream
    sudo systemctl stop video-stream
    echo "video-stream disabled and stopped"

# Show video stream logs
stream-log:
    sudo journalctl -u video-stream -f


# ============================================================================
# Internal Helpers
# ============================================================================

# Main menu
_menu:
    #!/usr/bin/env bash
    echo "Select Language:"
    echo "  1. Python [default]"
    echo "  2. C++"
    echo "  3. Rust"
    echo ""
    read -p "Choice [1]: " choice
    choice=${choice:-1}

    case $choice in
        1) just python-run ;;
        2) just cpp-run ;;
        3) just rust-run ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

# Connection selection helper (MAVSDK format with :// separator)
_get-connection format="mavsdk":
    #!/usr/bin/env bash
    # Auto-detect USB device
    USB_DEV=$(ls /dev/ttyACM* 2>/dev/null | head -1)
    USB_DEV=${USB_DEV:-{{USB_PORT}}}

    echo "Select Connection:" >&2
    echo "  1. UDP SITL [default]" >&2
    echo "  2. USB Serial ($USB_DEV, {{USB_BAUD}} baud)" >&2
    echo "  3. TELEM2 ({{UART_PORT}}, {{UART_BAUD}} baud)" >&2
    echo "" >&2
    read -p "Choice [1]: " choice
    choice=${choice:-1}

    case $choice in
        1) echo "udpin://0.0.0.0:14540" ;;
        2) echo "serial://$USB_DEV:{{USB_BAUD}}" ;;
        3) echo "serial://{{UART_PORT}}:{{UART_BAUD}}" ;;
        *) echo "Invalid choice" >&2; exit 1 ;;
    esac

# Parse serial connection string to port and baud (for pymavlink)
_parse-serial-connection connection:
    #!/usr/bin/env bash
    PORT=$(echo "{{connection}}" | sed 's|serial://||;s|:.*||')
    BAUD=$(echo "{{connection}}" | sed 's|.*:||')
    echo "$PORT $BAUD"

# Python interactive menu
_python-interactive:
    #!/usr/bin/env bash
    cd python
    . venv/bin/activate

    DRONE_ADDRESS=$(just _get-connection)

    echo ""
    echo "Commands:"
    echo "  1. Shell [default]"
    echo "  2. Takeoff"
    echo "  3. Offboard hover"
    echo ""
    echo "Telemetry:"
    echo "  4. EKF status (MAVLink)"
    echo "  5. EKF monitor (MAVLink)"
    echo "  6. EKF status (MAVSDK)"
    echo "  7. EKF monitor (MAVSDK)"
    echo "  8. RC status"
    echo "  9. RC monitor"
    echo "  10. Heartbeat monitor"
    echo ""
    echo "Configuration:"
    echo "  11. Compare parameters with defaults"
    echo "  12. Configure TELEM2"
    echo "  13. Reset parameters to defaults"
    echo "  14. Reboot Pixhawk"
    echo ""
    read -p "Choice [1]: " choice
    choice=${choice:-1}

    case $choice in
        1)
            read -p "Shell command: " cmd
            [ -z "$cmd" ] && echo "No command provided" && exit 1
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main shell "$cmd"
            ;;
        2) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main takeoff ;;
        3) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main offboard-hover ;;
        4) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-status ;;
        5)
            read -p "Duration [{{DEFAULT_DURATION}}]: " duration
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-monitor "${duration:-{{DEFAULT_DURATION}}}"
            ;;
        6) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main mavsdk-ekf-status ;;
        7)
            read -p "Duration [{{DEFAULT_DURATION}}]: " duration
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main mavsdk-ekf-monitor "${duration:-{{DEFAULT_DURATION}}}"
            ;;
        8) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-status ;;
        9)
            read -p "Duration [{{DEFAULT_DURATION}}]: " duration
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-monitor "${duration:-{{DEFAULT_DURATION}}}"
            ;;
        10)
            read -p "Duration [{{DEFAULT_DURATION}}]: " duration
            python -m src.main heartbeat-monitor "$DRONE_ADDRESS" "${duration:-{{DEFAULT_DURATION}}}"
            ;;
        11)
            read -r PORT BAUD <<< $(just _parse-serial-connection "$DRONE_ADDRESS")
            python -m src.main compare-params "$PORT" "$BAUD"
            ;;
        12)
            read -r PORT BAUD <<< $(just _parse-serial-connection "$DRONE_ADDRESS")
            python -m src.main configure-telem2 "$PORT" "$BAUD"
            if [ $? -eq 0 ]; then
                echo ""
                read -p "Reboot now to apply changes? [Y/n]: " reboot_choice
                if [ -z "$reboot_choice" ] || [ "$reboot_choice" = "y" ] || [ "$reboot_choice" = "Y" ]; then
                    python -m src.main reboot "$PORT" "$BAUD"
                fi
            fi
            ;;
        13)
            read -r PORT BAUD <<< $(just _parse-serial-connection "$DRONE_ADDRESS")
            python -m src.main reset-params "$PORT" "$BAUD"
            if [ $? -eq 0 ]; then
                echo ""
                read -p "Reboot now to apply changes? [Y/n]: " reboot_choice
                if [ -z "$reboot_choice" ] || [ "$reboot_choice" = "y" ] || [ "$reboot_choice" = "Y" ]; then
                    python -m src.main reboot "$PORT" "$BAUD"
                fi
            fi
            ;;
        14)
            read -r PORT BAUD <<< $(just _parse-serial-connection "$DRONE_ADDRESS")
            python -m src.main reboot "$PORT" "$BAUD"
            ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

# C++ interactive menu
_cpp-interactive:
    #!/usr/bin/env bash
    cd cpp/build

    echo ""
    echo "Examples:"
    echo "  1. Heartbeat monitor (MAVSDK) [default]"
    echo "  2. RC monitor (MAVLink)"
    echo ""
    read -p "Choice [1]: " example
    example=${example:-1}

    echo ""
    echo "Device:"
    echo "  1. USB ({{USB_PORT}}, {{USB_BAUD}} baud) [default]"
    echo "  2. TELEM2 ({{UART_PORT}}, {{UART_BAUD}} baud)"
    echo ""
    read -p "Choice [1]: " device
    device=${device:-1}

    case $device in
        1) DEV="{{USB_PORT}}"; BAUD="{{USB_BAUD}}" ;;
        2) DEV="{{UART_PORT}}"; BAUD="{{UART_BAUD}}" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

    case $example in
        1) DRONE_ADDRESS="serial://${DEV}:${BAUD}" ./heartbeat_monitor ;;
        2) DRONE_ADDRESS="serial:${DEV}:${BAUD}" ./main rc-monitor ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

# Rust interactive menu
_rust-interactive:
    #!/usr/bin/env bash
    cd rust

    CONNECTION=$(just _get-connection)

    echo ""
    echo "Message Filter:"
    echo "  1. All messages [default]"
    echo "  2. GLOBAL_POSITION_INT"
    echo "  3. ATTITUDE"
    echo "  4. HEARTBEAT"
    echo "  5. Custom message"
    echo ""
    read -p "Choice [1]: " choice
    choice=${choice:-1}

    case $choice in
        1) cargo run --release -- "$CONNECTION" ;;
        2) cargo run --release -- "$CONNECTION" --messages "GLOBAL_POSITION_INT" ;;
        3) cargo run --release -- "$CONNECTION" --messages "ATTITUDE" ;;
        4) cargo run --release -- "$CONNECTION" --messages "HEARTBEAT" ;;
        5)
            read -p "Message name: " msg
            [ -z "$msg" ] && echo "No message provided" && exit 1
            cargo run --release -- "$CONNECTION" --messages "$msg"
            ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
