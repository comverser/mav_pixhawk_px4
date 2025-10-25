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
    echo "Select Connection:" >&2
    echo "  1. UDP SITL [default]" >&2
    echo "  2. USB Serial (/dev/ttyACM0, 57600 baud)" >&2
    echo "  3. TELEM2 (/dev/ttyAMA0, 921600 baud)" >&2
    echo "" >&2
    read -p "Choice [1]: " choice
    choice=${choice:-1}

    case $choice in
        1) echo "udpin://0.0.0.0:14540" ;;
        2) echo "serial:///dev/ttyACM0:57600" ;;
        3) echo "serial:///dev/ttyAMA0:921600" ;;
        *) echo "Invalid choice" >&2; exit 1 ;;
    esac

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
    echo "  4. EKF status"
    echo "  5. EKF monitor"
    echo "  6. RC status"
    echo "  7. RC monitor"
    echo "  8. Heartbeat monitor"
    echo ""
    echo "Configuration:"
    echo "  9. Configure TELEM2"
    echo "  10. Reset parameters to defaults"
    echo "  11. Reboot Pixhawk"
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
            read -p "Duration [10]: " duration
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-monitor "${duration:-10}"
            ;;
        6) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-status ;;
        7)
            read -p "Duration [10]: " duration
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-monitor "${duration:-10}"
            ;;
        8)
            read -p "Duration [10]: " duration
            CONNECTION=$(echo "$DRONE_ADDRESS" | sed 's|serial://||;s|:/|/|;s|:\([0-9]*\)$|,\1|')
            python -m src.main heartbeat-monitor "$CONNECTION" "${duration:-10}"
            ;;
        9) python -m src.main configure-telem2 /dev/ttyACM0 57600 ;;
        10) python -m src.main reset-params /dev/ttyACM0 57600 ;;
        11) python -m src.main reboot /dev/ttyACM0 57600 ;;
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
    echo "  1. USB (/dev/ttyACM0, 57600 baud) [default]"
    echo "  2. TELEM2 (/dev/ttyAMA0, 921600 baud)"
    echo ""
    read -p "Choice [1]: " device
    device=${device:-1}

    case $device in
        1) DEV="/dev/ttyACM0"; BAUD="57600" ;;
        2) DEV="/dev/ttyAMA0"; BAUD="921600" ;;
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
