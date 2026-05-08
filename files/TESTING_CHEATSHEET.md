# Jetson + ARK FC Testing Cheat Sheet

## Quick Setup (5 minutes)

### 1. Check Hardware
```bash
bash ~/quick_test.sh
# Or manually:
lsusb | grep -i ark          # Should find ARK device
ls -la /dev/ttyACM*          # Should show /dev/ttyACM0
```

### 2. Fix Permissions (if needed)
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### 3. Launch MAVROS2
```bash
# Terminal 1
cd ~/ros2_ws && source install/setup.bash
ros2 launch drone_control mavros_ark.launch.py
# Should see: [MAVROS] FCU Connected
```

### 4. Check Signals
```bash
# Terminal 2: Simple heartbeat check
ros2 topic echo /mavros/state

# Terminal 3: Monitor everything
python3 ~/signal_monitor.py

# Terminal 3 (alternative): Low-level sniffer
python3 ~/mavlink_sniffer.py
```

---

## Testing Sequence

### Step A: Verify Heartbeat (Mandatory)
```bash
ros2 topic echo /mavros/state | head -20

# Should see:
# connected: true
# armed: false
# mode: 'STABILIZE' (or whatever mode is set)
```

### Step B: Verify IMU Data
```bash
ros2 topic echo /mavros/imu/data | head -20

# Should see:
# linear_acceleration: {x: 0.0, y: 0.0, z: 9.81}  (or close to 9.81)
# angular_velocity: {x: ~0.0, y: ~0.0, z: ~0.0}
```

### Step C: Test Position Publishing
```bash
# Terminal 3: Watch for position messages
ros2 topic echo /mavros/local_position/pose

# Terminal 2: Publish a setpoint from your drone code
# Should see position update after ~0.5 seconds
```

### Step D: Run Full Validation
```bash
python3 ~/signal_validator.py

# Should confirm:
# heartbeat ✓
# position_setpoint ✓  (if your code publishes)
# attitude_control ✓   (if using attitude commands)
# arm_command ✓
# mode_change ✓
```

---

## Common Commands

### Check Connection
```bash
# Is MAVROS connected to FC?
ros2 service call /mavros/cmd/land mavros_msgs/srv/CommandTOL "{}"
# If accepted = connected ✓

# What mode is drone in?
ros2 topic echo /mavros/state --once | grep mode

# Is drone armed?
ros2 topic echo /mavros/state --once | grep armed
```

### Send Commands
```bash
# Set mode to GUIDED
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"

# Arm drone
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"

# Disarm
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: false}"

# Land
ros2 service call /mavros/cmd/land mavros_msgs/srv/CommandTOL \
  "{min_pitch: 0.0, yaw: 0.0, latitude: 0.0, longitude: 0.0, altitude: 0.0}"
```

### Publish Setpoint (for autonomous control)
```python
# Python code to test
import rclpy
from geometry_msgs.msg import PoseStamped

rclpy.init()
node = rclpy.create_node('test_pub')
pub = node.create_publisher(PoseStamped, '/mavros/setpoint_position/local', 10)

sp = PoseStamped()
sp.pose.position.x = 0.0
sp.pose.position.y = 0.0
sp.pose.position.z = 1.0  # 1 meter up
sp.pose.orientation.w = 1.0

for _ in range(100):
    pub.publish(sp)
    rclpy.spin_once(node, timeout_sec=0.01)
```

---

## Troubleshooting

### "No heartbeat / Connection refused"
```bash
# 1. Check FC is powered
# 2. Check USB cable (try different port)
# 3. Try manual connection:
python3 ~/mavlink_sniffer.py
# If no output → hardware issue
# If output → ROS2/MAVROS issue

# 4. Verify baudrate (should be 115200)
# Try other rates if FC is older: 57600, 230400

# 5. Restart FC by power cycling (disconnect, wait 5s, reconnect)
```

### "Permission denied: /dev/ttyACM0"
```bash
# Option 1: Add to dialout group
sudo usermod -a -G dialout $USER
# Then log out/in

# Option 2: Temporary fix
sudo chmod 666 /dev/ttyACM0

# Option 3: Permanent udev rule
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/99-ark-fc.rules
sudo udevadm control --reload
```

### "Drone won't arm / Commands ignored"
```bash
# Check armed state first
ros2 topic echo /mavros/state --once

# If armed=false, try:
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"

# If still fails, check:
# 1. Mode must be GUIDED, ACRO, or OFFBOARD
# 2. Calibration: accelerometer, compass, radio
# 3. RC failsafe not triggered
# 4. Battery voltage sufficient
# 5. Props may be on (if it says "Reason: Already armed")
```

### "Signals received but values look wrong"
```bash
# 1. Check sensor calibration
# Open Mission Planner / QGroundControl → Calibrate Sensors

# 2. Verify frame alignment
# Ensure IMU/sensors same orientation as FC

# 3. Check ROS2 transforms
ros2 run tf2_tools view_frames

# 4. Compare with QGroundControl
# Launch QGroundControl, compare telemetry side-by-side
```

---

## File Locations

| File | Purpose |
|------|---------|
| `~/jetson_ark_setup_guide.md` | Full detailed guide |
| `~/quick_test.sh` | Hardware checks |
| `~/signal_monitor.py` | Real-time signal display (curses) |
| `~/mavlink_sniffer.py` | Low-level packet capture |
| `~/signal_validator.py` | Test & validate all signals |
| `~/verify_connection.py` | Basic connectivity check |
| `~/test_arm_takeoff.py` | Example arm/takeoff code |
| `~/ros2_ws/src/drone_control/launch/mavros_ark.launch.py` | MAVROS2 launcher |

---

## Safety Checklist Before Flight Test

- [ ] Propellers removed during bench testing
- [ ] Drone tethered or in containment
- [ ] Battery fully charged
- [ ] All sensors calibrated (accel, compass, level)
- [ ] Heartbeat confirmed with /mavros/state
- [ ] IMU data looks reasonable (9.81 m/s² on Z when level)
- [ ] Arming & mode change commands work
- [ ] Setpoints publishing correctly
- [ ] RC transmitter in range and on
- [ ] Geofence and failsafe configured

---

## Typical Output (Everything Working)

```
[MAVROS] FCU Connected
topic: /mavros/state
  connected: true
  armed: false
  mode: 'STABILIZE'

topic: /mavros/imu/data
  linear_acceleration: {x: -0.05, y: 0.02, z: 9.82}
  angular_velocity: {x: -0.001, y: 0.000, z: 0.001}

topic: /mavros/local_position/pose
  position: {x: 0.001, y: -0.002, z: 0.0}
  orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}

[TEST] Sending arm command...
✓ Arm command accepted

[TEST] Sending mode change (GUIDED)...
✓ Mode change command sent
```

---

## Next: Integrate with Your Code

Once signals verified, integrate MAVROS2 into your autonomous stack:

```python
# Example: Integrate with SUPER/DarkNet3D workflow
class DroneAutonomy(Node):
    def __init__(self):
        super().__init__('drone_autonomy')
        
        # Sensors
        self.pose_sub = self.create_subscription(PoseStamped, '/mavros/local_position/pose', ...)
        self.imu_sub = self.create_subscription(Imu, '/mavros/imu/data', ...)
        
        # Controls
        self.sp_pub = self.create_publisher(PoseStamped, '/mavros/setpoint_position/local', 10)
        
        # Services
        self.arm_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        
        # Now integrate with perception + planning
        self.perception_node = DarkNet3DPerception()
        self.planner_node = SUPERPlanner()
```

Good luck! 🚁
