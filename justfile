# ============================================================================
# Global Commands
# ============================================================================

default: menu

# Setup: Pull latest changes and update submodules
setup:
    git pull --rebase --autostash
    git submodule update --init --remote

# Main interactive menu
menu: setup
    @just _main-menu

# Interactive run - choose language and command
run: setup
    @just _select-language

# Configure Pixhawk interactively
config: python-setup
    @just _config-interactive

# Clean all build artifacts (Python, C++, Rust)
clean: python-clean cpp-clean rust-clean

# ============================================================================
# Python
# ============================================================================

# Setup Python environment
python-setup:
    @cd python && test -d venv || python3 -m venv venv
    @cd python && venv/bin/pip install -q -r requirements.txt

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

# --- Main Menus ---

_main-menu:
    #!/usr/bin/env bash
    echo "Select Option:"
    echo "  1. Python [default]"
    echo "  2. C++"
    echo "  3. Rust"
    echo "  4. Configure Pixhawk"
    echo ""
    read -p "Choice [1]: " main_choice
    main_choice=${main_choice:-1}

    case $main_choice in
        1) just python-run ;;
        2) just cpp-run ;;
        3) just rust-run ;;
        4) just _config-interactive ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

_config-interactive:
    #!/usr/bin/env bash
    echo "Pixhawk Configuration:"
    echo "  1. Configure TELEM 2 (921600 baud) [default]"
    echo "  2. List parameters (filter: MAV/SER)"
    echo "  3. Reboot Pixhawk"
    echo ""
    read -p "Choice [1]: " config_choice
    config_choice=${config_choice:-1}

    case $config_choice in
        1)
            echo ""
            python/venv/bin/python3 config/configure_telem2.py
            ;;
        2)
            echo ""
            echo "Listing MAVLink and Serial parameters..."
            python/venv/bin/python3 config/list_all_params.py MAV
            echo ""
            python/venv/bin/python3 config/list_all_params.py SER
            ;;
        3)
            echo ""
            python/venv/bin/python3 config/reboot_pixhawk.py
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

# --- Common Helpers ---

_select-language:
    #!/usr/bin/env bash
    echo "Select Language:"
    echo "  1. Python [default]"
    echo "  2. C++"
    echo "  3. Rust"
    echo ""
    read -p "Choice [1]: " lang_choice
    lang_choice=${lang_choice:-1}

    case $lang_choice in
        1) just python-run ;;
        2) just cpp-run ;;
        3) just rust-run ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

_get-connection format="python":
    #!/usr/bin/env bash
    # Print prompts to stderr so they don't get captured
    echo "Select Connection:" >&2
    echo "  1. UDP SITL [default]" >&2
    echo "  2. Serial" >&2
    echo "" >&2
    read -p "Choice [1]: " conn_choice
    conn_choice=${conn_choice:-1}

    case $conn_choice in
        1)
            if [ "{{format}}" = "python" ]; then
                echo "udpin://0.0.0.0:14540"
            else
                echo "udpin:0.0.0.0:14540"
            fi
            ;;
        2)
            echo "serial:/dev/ttyACM0:57600"
            ;;
        *)
            echo "Invalid choice" >&2
            exit 1
            ;;
    esac

# --- Language Interactive ---

_python-interactive:
    #!/usr/bin/env bash
    cd python
    . venv/bin/activate

    # Get connection
    DRONE_ADDRESS=$(just _get-connection python)

    # Get command
    echo ""
    echo "Select Command:"
    echo "  Commands:"
    echo "    1. Shell [default]"
    echo "    2. Takeoff"
    echo "    3. Offboard hover"
    echo ""
    echo "  Telemetry:"
    echo "    4. EKF status"
    echo "    5. EKF monitor"
    echo "    6. RC status"
    echo "    7. RC monitor"
    echo ""
    read -p "Choice [1]: " cmd_choice
    cmd_choice=${cmd_choice:-1}

    case $cmd_choice in
        1)
            read -p "Shell command: " shell_cmd
            [ -z "$shell_cmd" ] && echo "No command provided" && exit 1
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main shell "$shell_cmd"
            ;;
        2) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main takeoff ;;
        3) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main offboard-hover ;;
        4) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-status ;;
        5)
            read -p "Duration [10]: " duration
            duration=${duration:-10}
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-monitor "$duration"
            ;;
        6) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-status ;;
        7)
            read -p "Duration [10]: " duration
            duration=${duration:-10}
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-monitor "$duration"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

_cpp-interactive:
    #!/usr/bin/env bash
    cd cpp/build

    # Select example
    echo ""
    echo "Select Example:"
    echo "  1. Heartbeat monitor (MAVSDK) [default]"
    echo "  2. RC monitor (MAVLink)"
    echo ""
    read -p "Choice [1]: " example_choice
    example_choice=${example_choice:-1}

    # Select serial device
    echo ""
    echo "Select Serial Device:"
    echo "  1. /dev/ttyACM0 (USB, 57600 baud) [default]"
    echo "  2. /dev/ttyAMA0 (TELEM 2, 921600 baud)"
    echo ""
    read -p "Choice [1]: " device_choice
    device_choice=${device_choice:-1}

    case $device_choice in
        1)
            DEVICE="/dev/ttyACM0"
            BAUDRATE="57600"
            ;;
        2)
            DEVICE="/dev/ttyAMA0"
            BAUDRATE="921600"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

    # Run selected example
    case $example_choice in
        1)
            # MAVSDK: format is serial:///dev/ttyXXX:baudrate
            DRONE_ADDRESS="serial://${DEVICE}:${BAUDRATE}" ./heartbeat_monitor
            ;;
        2)
            # MAVLink: format is serial:/dev/ttyXXX:baudrate
            DRONE_ADDRESS="serial:${DEVICE}:${BAUDRATE}" ./main rc-monitor
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

_rust-interactive:
    #!/usr/bin/env bash
    cd rust

    # Get connection
    CONNECTION=$(just _get-connection rust)

    # Get message filter
    echo ""
    echo "Select Message Filter:"
    echo "  1. All messages [default]"
    echo "  2. GLOBAL_POSITION_INT"
    echo "  3. ATTITUDE"
    echo "  4. HEARTBEAT"
    echo "  5. Custom message"
    echo ""
    read -p "Choice [1]: " msg_choice
    msg_choice=${msg_choice:-1}

    case $msg_choice in
        1) cargo run --release -- "$CONNECTION" ;;
        2) cargo run --release -- "$CONNECTION" --messages "GLOBAL_POSITION_INT" ;;
        3) cargo run --release -- "$CONNECTION" --messages "ATTITUDE" ;;
        4) cargo run --release -- "$CONNECTION" --messages "HEARTBEAT" ;;
        5)
            read -p "Message name: " MESSAGE
            [ -z "$MESSAGE" ] && echo "No message provided" && exit 1
            cargo run --release -- "$CONNECTION" --messages "$MESSAGE"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
