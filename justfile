# ============================================================================
# Global Commands
# ============================================================================

default: menu

# Main interactive menu
menu: setup
    @just _main-menu

# Interactive run - choose language and command
run: setup
    @just _select-language

# Setup all environments
setup:
    git pull --rebase --autostash
    git submodule update --init --remote

# Interactive Pixhawk configuration
config: python-setup
    @just _config-interactive

# Clean all build artifacts
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

# Build C++ project
cpp-build:
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
        1)
            just python-run
            ;;
        2)
            just cpp-run
            ;;
        3)
            just rust-run
            ;;
        4)
            just _config-interactive
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

# Interactive Pixhawk configuration menu
_config-interactive:
    #!/usr/bin/env bash
    echo "Pixhawk Configuration:"
    echo "  1. List parameters (filter: MAV/SER)"
    echo "  2. Configure TELEM 2 (921600 baud) [default]"
    echo "  3. Reboot Pixhawk"
    echo ""
    read -p "Choice [2]: " config_choice
    config_choice=${config_choice:-2}

    case $config_choice in
        1)
            echo ""
            echo "Listing MAVLink and Serial parameters..."
            python/venv/bin/python3 config/list_all_params.py MAV
            echo ""
            python/venv/bin/python3 config/list_all_params.py SER
            ;;
        2)
            echo ""
            python/venv/bin/python3 config/configure_telem2.py
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

# Select language interactively
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

# Get connection type interactively (returns format for given language)
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

# Python interactive command selection
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
        2)
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main takeoff
            ;;
        3)
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main offboard-hover
            ;;
        4)
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-status
            ;;
        5)
            read -p "Duration [10]: " duration
            duration=${duration:-10}
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main ekf-monitor "$duration"
            ;;
        6)
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-status
            ;;
        7)
            read -p "Duration [10]: " duration
            duration=${duration:-10}
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main rc-monitor "$duration"
            ;;
        *)
            echo "Invalid choice"; exit 1
            ;;
    esac

# C++ interactive command selection
_cpp-interactive:
    #!/usr/bin/env bash
    cd cpp/build

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
            DRONE_ADDRESS="serial:/dev/ttyACM0:57600"
            ;;
        2)
            DRONE_ADDRESS="serial:/dev/ttyAMA0:921600"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac

    # Run RC monitor
    DRONE_ADDRESS="$DRONE_ADDRESS" ./main rc-monitor

    # TODO: Add MAVSDK implementation option

# Rust interactive command selection
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
        1)
            cargo run --release -- "$CONNECTION"
            ;;
        2)
            cargo run --release -- "$CONNECTION" --messages "GLOBAL_POSITION_INT"
            ;;
        3)
            cargo run --release -- "$CONNECTION" --messages "ATTITUDE"
            ;;
        4)
            cargo run --release -- "$CONNECTION" --messages "HEARTBEAT"
            ;;
        5)
            read -p "Message name: " MESSAGE
            [ -z "$MESSAGE" ] && echo "No message provided" && exit 1
            cargo run --release -- "$CONNECTION" --messages "$MESSAGE"
            ;;
        *)
            echo "Invalid choice"; exit 1
            ;;
    esac

