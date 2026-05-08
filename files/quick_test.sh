#!/bin/bash
# Quick Test: Jetson + ARK FC Connection Verification
# Usage: bash quick_test.sh

set -e

echo "=========================================="
echo "JETSON + ARK FC QUICK TEST"
echo "=========================================="
echo ""

# Step 1: Hardware check
echo "[1/5] Checking hardware connection..."
if lsusb | grep -qi "ark\|serial\|uart"; then
    echo "  ✓ USB device detected"
else
    echo "  ⚠ No ARK FC USB detected - check cable"
fi

# Check serial port
if [ -e /dev/ttyACM0 ]; then
    echo "  ✓ Serial port /dev/ttyACM0 exists"
    SERIAL_PORT="/dev/ttyACM0"
elif [ -e /dev/ttyUSB0 ]; then
    echo "  ✓ Serial port /dev/ttyUSB0 exists"
    SERIAL_PORT="/dev/ttyUSB0"
else
    echo "  ✗ No serial port found!"
    echo "  → Try: sudo dmesg | tail -20"
    exit 1
fi

# Step 2: Permission check
echo ""
echo "[2/5] Checking serial permissions..."
if [ -r "$SERIAL_PORT" ] && [ -w "$SERIAL_PORT" ]; then
    echo "  ✓ $SERIAL_PORT readable and writable"
else
    echo "  ✗ Cannot access $SERIAL_PORT"
    echo "  → Fix: sudo usermod -a -G dialout \$USER && logout/login"
    exit 1
fi

# Step 3: ROS2 check
echo ""
echo "[3/5] Checking ROS2 environment..."
if [ -z "$ROS_DOMAIN_ID" ]; then
    echo "  ⚠ ROS_DOMAIN_ID not set (using default: 0)"
else
    echo "  ✓ ROS_DOMAIN_ID = $ROS_DOMAIN_ID"
fi

if command -v ros2 &> /dev/null; then
    echo "  ✓ ROS2 installed: $(ros2 --version | head -1)"
else
    echo "  ✗ ROS2 not found"
    exit 1
fi

# Step 4: MAVProxy test (optional)
echo ""
echo "[4/5] Testing MAVLink connection..."
if command -v mavproxy.py &> /dev/null; then
    echo "  ✓ MAVProxy available"
    echo "  → To test: mavproxy.py --master=$SERIAL_PORT --baudrate=115200"
else
    echo "  ⚠ MAVProxy not installed (optional for GUI testing)"
    echo "  → Install: pip install MAVProxy pymavlink"
fi

# Step 5: MAVROS2 check
echo ""
echo "[5/5] Checking MAVROS2..."
if ros2 pkg list | grep -q mavros; then
    echo "  ✓ MAVROS2 is installed"
else
    echo "  ✗ MAVROS2 not found"
    echo "  → Install: sudo apt install ros-humble-mavros ros-humble-mavros-extras"
    exit 1
fi

echo ""
echo "=========================================="
echo "READY TO LAUNCH MAVROS2"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Terminal 1: ros2 launch drone_control mavros_ark.launch.py"
echo "  2. Terminal 2: python3 ~/signal_monitor.py"
echo "  3. Monitor for HEARTBEAT and position updates"
echo ""
echo "Troubleshooting:"
echo "  • No heartbeat: check FC power, USB cable, baudrate"
echo "  • Permission denied: run 'sudo usermod -a -G dialout \$USER'"
echo "  • No /dev/ttyACM0: try /dev/ttyUSB0 or check dmesg"
echo ""
