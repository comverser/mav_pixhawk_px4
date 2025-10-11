# ============================================================================
# Global Commands
# ============================================================================

default: run

# Interactive run - choose language and command
run: setup
    @just _select-language

# Setup all environments
setup:
    git pull --rebase --autostash

# Clean all build artifacts
clean: python-clean

# ============================================================================
# Python
# ============================================================================

# Run Python examples interactively
python-run: python-setup
    @just _python-interactive

# Setup Python environment
python-setup:
    @cd python && test -d venv || python3 -m venv venv
    @cd python && venv/bin/pip install -q -r requirements.txt

# Clean Python artifacts
python-clean:
    @rm -rf python/venv
    @find python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @find python -type f -name "*.pyc" -delete 2>/dev/null || true
    @find python -type f -name "*.pyo" -delete 2>/dev/null || true

# ============================================================================
# Internal Helpers
# ============================================================================

# Select language interactively
_select-language:
    #!/usr/bin/env bash
    echo "Select Language:"
    echo "  1. Python [default]"
    echo ""
    read -p "Choice [1]: " lang_choice
    lang_choice=${lang_choice:-1}

    case $lang_choice in
        1) just python-run ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

# Python interactive command selection
_python-interactive:
    #!/usr/bin/env bash
    cd python
    . venv/bin/activate

    # Get connection
    echo "Select Connection:"
    echo "  1. UDP SITL [default]"
    echo "  2. Serial"
    echo "  3. Custom"
    echo ""
    read -p "Choice [1]: " conn_choice
    conn_choice=${conn_choice:-1}

    case $conn_choice in
        1) DRONE_ADDRESS="udpin://0.0.0.0:14540" ;;
        2) DRONE_ADDRESS="serial:/dev/ttyACM0:57600" ;;
        3)
            read -p "Connection string: " DRONE_ADDRESS
            [ -z "$DRONE_ADDRESS" ] && echo "Invalid connection" && exit 1
            ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

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

