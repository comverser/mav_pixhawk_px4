default: run

run: setup
    #!/usr/bin/env bash
    . venv/bin/activate

    echo "Connection:"
    echo "1. UDP SITL [default]"
    echo "2. Serial"
    echo "3. Custom"
    read -p "Choice [1]: " conn_choice
    conn_choice=${conn_choice:-1}
    case $conn_choice in
        1) DRONE_ADDRESS="udpin://0.0.0.0:14540" ;;
        2) DRONE_ADDRESS="serial:/dev/ttyACM0:57600" ;;
        3) read -p "Connection string: " DRONE_ADDRESS ;;
        *) echo "Invalid"; exit 1 ;;
    esac

    echo ""
    echo "Commands:"
    echo "1. Shell [default]"
    echo "2. Takeoff"
    echo "3. Offboard hover"
    echo ""
    echo "Telemetry:"
    echo "4. EKF status"
    echo "5. EKF monitor"
    echo "6. RC status"
    echo "7. RC monitor"
    read -p "Choice [1]: " cmd_choice
    cmd_choice=${cmd_choice:-1}
    case $cmd_choice in
        1)
            read -p "Shell command: " shell_cmd
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main shell "$shell_cmd"
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
        *) echo "Invalid"; exit 1 ;;
    esac

# Setup environment
setup:
    git pull --rebase --autostash
    @test -d venv || python3 -m venv venv
    @venv/bin/pip install -q -r requirements.txt

# Clean build artifacts and caches
clean:
    rm -rf venv
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
