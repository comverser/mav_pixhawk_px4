default: run

# Interactive run
run: setup
    #!/usr/bin/env bash
    . venv/bin/activate

    # Connection selection
    echo "Select connection type:"
    echo "1. UDP (SITL) - udp://:14540 [default]"
    echo "2. Serial (Hardware) - serial:/dev/ttyACM0:57600"
    echo "3. Custom"
    read -p "Choice (1-3) [1]: " conn_choice
    conn_choice=${conn_choice:-1}
    case $conn_choice in
        1) DRONE_ADDRESS="udp://:14540" ;;
        2) DRONE_ADDRESS="serial:/dev/ttyACM0:57600" ;;
        3) read -p "Enter connection string: " DRONE_ADDRESS ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

    # Command selection
    echo ""
    echo "Select command:"
    echo "1. Shell command [default]"
    echo "2. Takeoff"
    read -p "Choice (1-2) [1]: " cmd_choice
    cmd_choice=${cmd_choice:-1}
    case $cmd_choice in
        1)
            read -p "Enter shell command: " shell_cmd
            DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main shell "$shell_cmd"
            ;;
        2) DRONE_ADDRESS="$DRONE_ADDRESS" python -m src.main takeoff ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

# Setup environment
setup:
    @test -d venv || python3 -m venv venv
    @venv/bin/pip install -q -r requirements.txt

# Clean
clean:
    rm -rf venv
