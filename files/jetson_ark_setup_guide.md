# Jetson Orin Nano + ARK Flight Controller Integration Guide

## Overview
This guide covers hardware setup, MAVROS2 configuration, and signal verification for autonomous drone control.

---

## Part 1: Hardware Setup

### Serial Connection (USB/UART)
**ARK to Jetson Options:**
1. **USB-C (Recommended):** ARK's USB-C port → Jetson USB-C port
   - No additional components needed
   - Automatic baudrate detection (typically 115200 bps)
   - Device appears as `/dev/ttyACM0`

2. **UART Breakout (Alternative):**
   - ARK UART TX/RX pins → USB-UART adapter → Jetson USB
   - Adapter: CH340G or similar (3.3V TTL)
   - Device appears as `/dev/ttyUSB0`

### Verification Steps
```bash
# Check if Jetson recognizes the FC
lsusb | grep -i ark
# or
ls -la /dev/ttyACM* /dev/ttyUSB*

# Check permission
sudo usermod -a -G dialout $USER
# Log out and back in for group change to take effect
```

---

## Part 2: MAVROS2 Installation & Configuration

### Install Dependencies
```bash
# Update and install prerequisites
sudo apt update
sudo apt install -y python3-rosdep python3-colcon-common-extensions \
  libopencv-dev python3-opencv ros-humble-mavros ros-humble-mavros-extras

# Geofence and geographic lib (MAVProxy fallback)
cd ~
wget https://raw.githubusercontent.com/mavlink/mavros/master/mavros/scripts/install_geographiclib_datasets.sh
sudo bash install_geographiclib_datasets.sh
```

### Install MAVProxy (Optional but Useful)
```bash
pip install MAVProxy pymavlink
```

---

## Part 3: MAVROS2 Launch & Configuration

### Create ROS2 Launch File
**File: `~/ros2_ws/src/drone_control/launch/mavros_ark.launch.py`**

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Configuration
    fcu_url = LaunchConfiguration('fcu_url', default='/dev/ttyACM0:115200')
    gcs_url = LaunchConfiguration('gcs_url', default='udp://@127.0.0.1:14550')
    
    # MAVROS node
    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        name='mavros',
        output='screen',
        parameters=[
            {'fcu_url': fcu_url},
            {'gcs_url': gcs_url},
            {'target_system_id': 1},
            {'target_component_id': 1},
            {'log_level': 'debug'},  # Change to 'info' in production
        ],
        remappings=[
            ('/mavros/setpoint_position/local', '/drone/setpoint_local'),
            ('/mavros/local_position/pose', '/drone/pose'),
            ('/mavros/imu/data', '/drone/imu'),
            ('/mavros/state', '/drone/state'),
        ]
    )
    
    return LaunchDescription([mavros_node])
```

### Create Minimal Config Override
**File: `~/.ros/mavros_pluginlist.yaml`** (if custom plugins needed)

```yaml
plugin_blacklist: []
plugin_whitelist: []
plugins:
  - sys_status
  - system_time
  - autopilot_version
  - local_position
  - global_position
  - position_target_local_ned
  - imu_pub
  - actuator_control
  - vfr_hud
```

---

## Part 4: Signal Verification Scripts

### 4a. Quick Connection Check
**File: `~/verify_connection.py`**

```python
#!/usr/bin/env python3
import subprocess
import time

print("=" * 60)
print("JETSON ↔ ARK FC CONNECTION CHECK")
print("=" * 60)

# 1. Hardware detection
print("\n[1] Hardware Detection:")
result = subprocess.run(['lsusb'], capture_output=True, text=True)
ark_found = any('ark' in line.lower() or 'serial' in line.lower() for line in result.stdout.split('\n'))
print(f"    ARK FC detected: {'✓ YES' if ark_found else '✗ NO'}")
print(f"    USB devices:\n{result.stdout}")

# 2. Serial port check
print("\n[2] Serial Port Check:")
result = subprocess.run(['ls', '-la', '/dev/ttyACM*', '/dev/ttyUSB*'], 
                       capture_output=True, text=True, shell=True)
print(result.stdout if result.stdout else "    No serial devices found")

# 3. Permission check
print("\n[3] Serial Port Permissions:")
result = subprocess.run(['id', '-Gn'], capture_output=True, text=True)
groups = result.stdout.strip().split()
print(f"    User groups: {', '.join(groups)}")
print(f"    dialout group: {'✓ YES' if 'dialout' in groups else '✗ NO (run: sudo usermod -a -G dialout $USER)'}")

print("\n" + "=" * 60)
```

### 4b. ROS2 MAVLink Signal Monitor
**File: `~/signal_monitor.py`**

```python
#!/usr/bin/env python3
"""
Real-time signal monitor for MAVROS2 + ARK FC
Displays: heartbeat, position, attitude, RC channels, mode, armed state
"""

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import State, Altitude, VFRHud
from sensor_msgs.msg import Imu, NavSatFix
from geometry_msgs.msg import PoseStamped
from mavros_msgs.srv import CommandBool, SetMode
from std_srvs.srv import Trigger
import curses
import time

class SignalMonitor(Node):
    def __init__(self):
        super().__init__('signal_monitor')
        
        # Subscribers
        self.state_sub = self.create_subscription(State, '/mavros/state', self.state_callback, 10)
        self.pose_sub = self.create_subscription(PoseStamped, '/mavros/local_position/pose', 
                                                  self.pose_callback, 10)
        self.imu_sub = self.create_subscription(Imu, '/mavros/imu/data', self.imu_callback, 10)
        self.vfr_sub = self.create_subscription(VFRHud, '/mavros/vfr_hud', self.vfr_callback, 10)
        self.alt_sub = self.create_subscription(Altitude, '/mavros/altitude', self.alt_callback, 10)
        
        # State storage
        self.state = None
        self.pose = None
        self.imu = None
        self.vfr = None
        self.altitude = None
        self.start_time = time.time()
        
    def state_callback(self, msg):
        self.state = {
            'connected': msg.connected,
            'armed': msg.armed,
            'mode': msg.mode,
            'system_status': msg.system_status
        }
    
    def pose_callback(self, msg):
        self.pose = {
            'x': msg.pose.position.x,
            'y': msg.pose.position.y,
            'z': msg.pose.position.z,
            'qx': msg.pose.orientation.x,
            'qy': msg.pose.orientation.y,
            'qz': msg.pose.orientation.z,
            'qw': msg.pose.orientation.w,
        }
    
    def imu_callback(self, msg):
        self.imu = {
            'ax': msg.linear_acceleration.x,
            'ay': msg.linear_acceleration.y,
            'az': msg.linear_acceleration.z,
            'gx': msg.angular_velocity.x,
            'gy': msg.angular_velocity.y,
            'gz': msg.angular_velocity.z,
        }
    
    def vfr_callback(self, msg):
        self.vfr = {
            'airspeed': msg.airspeed,
            'groundspeed': msg.groundspeed,
            'heading': msg.heading,
            'throttle': msg.throttle,
            'altitude': msg.altitude,
            'climb_rate': msg.climb_rate,
        }
    
    def alt_callback(self, msg):
        self.altitude = {
            'relative': msg.relative,
            'absolute': msg.absolute,
            'local': msg.local,
            'amsl': msg.amsl,
        }
    
    def print_status(self, stdscr):
        while True:
            try:
                stdscr.clear()
                h, w = stdscr.getmaxyx()
                elapsed = time.time() - self.start_time
                
                # Title
                title = f"MAVROS2 + ARK FC Signal Monitor | Elapsed: {elapsed:.1f}s"
                stdscr.addstr(0, 0, title, curses.color_pair(1) | curses.A_BOLD)
                
                line = 2
                
                # Heartbeat/Connection
                if self.state:
                    status_color = curses.color_pair(2) if self.state['connected'] else curses.color_pair(3)
                    stdscr.addstr(line, 0, "=== HEARTBEAT ===", curses.A_BOLD)
                    line += 1
                    stdscr.addstr(line, 0, f"  Connected: {self.state['connected']}", status_color)
                    line += 1
                    stdscr.addstr(line, 0, f"  Armed: {self.state['armed']}")
                    line += 1
                    stdscr.addstr(line, 0, f"  Mode: {self.state['mode']}")
                    line += 1
                    stdscr.addstr(line, 0, f"  System Status: {self.state['system_status']}")
                    line += 2
                
                # Position
                if self.pose:
                    stdscr.addstr(line, 0, "=== LOCAL POSITION (ENU) ===", curses.A_BOLD)
                    line += 1
                    stdscr.addstr(line, 0, f"  X: {self.pose['x']:8.3f} m  (East)")
                    line += 1
                    stdscr.addstr(line, 0, f"  Y: {self.pose['y']:8.3f} m  (North)")
                    line += 1
                    stdscr.addstr(line, 0, f"  Z: {self.pose['z']:8.3f} m  (Up)")
                    line += 2
                
                # Altitude
                if self.altitude:
                    stdscr.addstr(line, 0, "=== ALTITUDE ===", curses.A_BOLD)
                    line += 1
                    stdscr.addstr(line, 0, f"  Relative (AGL): {self.altitude['relative']:.2f} m")
                    line += 1
                    stdscr.addstr(line, 0, f"  Absolute (MSL): {self.altitude['absolute']:.2f} m")
                    line += 2
                
                # Velocity & Speed
                if self.vfr:
                    stdscr.addstr(line, 0, "=== VELOCITY ===", curses.A_BOLD)
                    line += 1
                    stdscr.addstr(line, 0, f"  Airspeed: {self.vfr['airspeed']:.2f} m/s")
                    line += 1
                    stdscr.addstr(line, 0, f"  Groundspeed: {self.vfr['groundspeed']:.2f} m/s")
                    line += 1
                    stdscr.addstr(line, 0, f"  Heading: {self.vfr['heading']}°")
                    line += 1
                    stdscr.addstr(line, 0, f"  Climb Rate: {self.vfr['climb_rate']:.2f} m/s")
                    line += 1
                    stdscr.addstr(line, 0, f"  Throttle: {self.vfr['throttle']}%")
                    line += 2
                
                # IMU
                if self.imu:
                    stdscr.addstr(line, 0, "=== IMU ===", curses.A_BOLD)
                    line += 1
                    stdscr.addstr(line, 0, f"  Accel: X={self.imu['ax']:6.2f}  Y={self.imu['ay']:6.2f}  Z={self.imu['az']:6.2f} m/s²")
                    line += 1
                    stdscr.addstr(line, 0, f"  Gyro:  X={self.imu['gx']:6.2f}  Y={self.imu['gy']:6.2f}  Z={self.imu['gz']:6.2f} rad/s")
                    line += 1
                
                # Warnings
                line += 1
                if not self.state or not self.state['connected']:
                    stdscr.addstr(line, 0, "⚠️  NO HEARTBEAT - Check serial connection!", curses.color_pair(3) | curses.A_BOLD)
                    line += 1
                
                stdscr.refresh()
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                stdscr.addstr(h-1, 0, f"Error: {str(e)}")
                stdscr.refresh()
                time.sleep(1)

def main():
    rclpy.init()
    monitor = SignalMonitor()
    
    # Wait for connection
    print("Waiting for MAVROS2 connection...")
    for i in range(30):
        if monitor.state and monitor.state['connected']:
            break
        time.sleep(0.5)
    
    try:
        curses.wrapper(monitor.print_status)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        monitor.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 4c. MAVLink Packet Sniffer (Low-level Verification)
**File: `~/mavlink_sniffer.py`**

```python
#!/usr/bin/env python3
"""
Low-level MAVLink packet sniffer
Directly monitors serial communication without ROS2
Useful for hardware-level debugging
"""

import serial
import argparse
from pymavlink.dialects.v20 import ardupilotmega as mavlink
import time
import sys

class MAVLinkSniffer:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.mav = mavlink.MAVLink(self.ser, srcSystem=255)
        self.msg_counts = {}
        self.start_time = time.time()
        
    def sniff(self, duration=60):
        print(f"Sniffing MAVLink packets on {self.ser.port} @ {self.ser.baudrate} bps")
        print(f"Duration: {duration}s (Press Ctrl+C to stop)")
        print("-" * 70)
        
        try:
            end_time = time.time() + duration
            while time.time() < end_time:
                msg = self.mav.recv_msg()
                if msg:
                    msg_type = msg.get_type()
                    
                    # Track message counts
                    self.msg_counts[msg_type] = self.msg_counts.get(msg_type, 0) + 1
                    
                    # Print selected messages
                    elapsed = time.time() - self.start_time
                    
                    if msg_type == 'HEARTBEAT':
                        print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                              f"Type: {msg.type:2d} | Autopilot: {msg.autopilot:2d} | "
                              f"System Status: {msg.system_status:2d} | Armed: {bool(msg.base_mode & 0x80)}")
                    
                    elif msg_type in ['ATTITUDE', 'ATTITUDE_QUATERNION']:
                        if msg_type == 'ATTITUDE':
                            print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                                  f"Roll: {msg.roll:7.2f}° | Pitch: {msg.pitch:7.2f}° | Yaw: {msg.yaw:7.2f}°")
                        else:
                            print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                                  f"Q: [{msg.q1:.3f}, {msg.q2:.3f}, {msg.q3:.3f}, {msg.q4:.3f}]")
                    
                    elif msg_type == 'LOCAL_POSITION_NED':
                        print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                              f"X: {msg.x:8.2f}m | Y: {msg.y:8.2f}m | Z: {msg.z:8.2f}m")
                    
                    elif msg_type == 'GLOBAL_POSITION_INT':
                        print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                              f"Lat: {msg.lat/1e7:10.6f} | Lon: {msg.lon/1e7:10.6f} | Alt: {msg.alt/1000:.1f}m")
                    
                    elif msg_type == 'VFR_HUD':
                        print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                              f"Airspeed: {msg.airspeed:6.2f}m/s | Throttle: {msg.throttle:3d}% | "
                              f"Alt: {msg.alt:7.1f}m | ClimbRate: {msg.climb:.2f}m/s")
                    
                    elif msg_type == 'RAW_IMU':
                        print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                              f"Accel: [{msg.xacc:6.0f}, {msg.yacc:6.0f}, {msg.zacc:6.0f}] | "
                              f"Gyro: [{msg.xgyro:7.1f}, {msg.ygyro:7.1f}, {msg.zgyro:7.1f}]")
                    
                    elif msg_type == 'RC_CHANNELS':
                        print(f"[{elapsed:6.2f}s] {msg_type:20s} | "
                              f"CH1-4: [{msg.chan1_raw:4d}, {msg.chan2_raw:4d}, {msg.chan3_raw:4d}, {msg.chan4_raw:4d}] ppm")
                    
        except KeyboardInterrupt:
            print("\n" + "-" * 70)
            print("Packet Summary:")
            for msg_type, count in sorted(self.msg_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {msg_type:25s}: {count:5d} packets")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.ser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MAVLink Packet Sniffer')
    parser.add_argument('--port', default='/dev/ttyACM0', help='Serial port (default: /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baudrate (default: 115200)')
    parser.add_argument('--duration', type=int, default=60, help='Sniff duration in seconds (default: 60)')
    
    args = parser.parse_args()
    
    sniffer = MAVLinkSniffer(port=args.port, baudrate=args.baud)
    sniffer.sniff(duration=args.duration)
```

---

## Part 5: Testing & Verification Workflow

### Step 0: Pre-Flight Checks
```bash
# 1. Verify serial connection
python3 ~/verify_connection.py

# 2. Check ARK FC firmware version (needs MAVProxy)
mavproxy.py --master=/dev/ttyACM0 --baudrate=115200 --out=udp:127.0.0.1:14550 &
# In MAVProxy: PARAM get STAT_FLTTIME
# Then: quit
```

### Step 1: Start MAVROS2
```bash
# Terminal 1: Launch MAVROS2
cd ~/ros2_ws
colcon build
source install/setup.bash
ros2 launch drone_control mavros_ark.launch.py fcu_url:=/dev/ttyACM0:115200
```

### Step 2a: Monitor Signals (ROS2 GUI)
```bash
# Terminal 2: Run signal monitor (requires curses)
python3 ~/signal_monitor.py
```

### Step 2b: Monitor Signals (Hardware Level)
```bash
# Terminal 2: Low-level MAVLink sniffer (no ROS2 needed)
python3 ~/mavlink_sniffer.py --port=/dev/ttyACM0 --baud=115200 --duration=120
```

### Step 3: Send Test Commands
```bash
# Terminal 3: ROS2 CLI or custom script
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"
```

---

## Part 6: Troubleshooting

### Issue: "No serial port found" / `/dev/ttyACM0: Permission denied`
```bash
# Solution 1: Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in

# Solution 2: Temporary sudo
sudo chmod 666 /dev/ttyACM0

# Solution 3: udev rule (permanent)
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="xxxx", ATTRS{idProduct}=="yyyy", MODE="0666"' | \
  sudo tee /etc/udev/rules.d/99-ark-fc.rules
sudo udevadm control --reload
```

### Issue: "No heartbeat from FCU" / MAVROS2 won't connect
```bash
# Check if FC is actually sending MAVLink
python3 ~/mavlink_sniffer.py

# If no packets: FC may be in bootloader or dead
# Try power cycling: disconnect USB, wait 5s, reconnect

# Check baudrate: ARK defaults to 115200 but verify with:
# - Firmware settings (Mission Planner / QGroundControl)
# - Try different rates if stuck: 57600, 230400

# Check USB cable: Try different port on Jetson
```

### Issue: Packets received but wrong values
```bash
# Verify sensor calibration on FC (accelerometer, compass, etc.)
# Check LiDAR/IMU alignment with FC frame
# Verify ROS2 frame transforms: ros2 run tf2_tools view_frames
```

### Issue: Commands sent but drone doesn't respond
```bash
# Verify armed state: monitor should show Armed: True
# Check flight mode: must be GUIDED, ACRO, or OFFBOARD
# Verify RC failsafe not triggered
# Test with QGroundControl first to isolate Jetson code issues
```

---

## Part 7: Code Example - Arming & Takeoff

**File: `~/test_arm_takeoff.py`**

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode
import time

class DroneController(Node):
    def __init__(self):
        super().__init__('drone_controller')
        
        self.state = None
        self.state_sub = self.create_subscription(State, '/mavros/state', self.state_cb, 10)
        
        # Services
        self.arm_srv = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.mode_srv = self.create_client(SetMode, '/mavros/set_mode')
        self.sp_pub = self.create_publisher(PoseStamped, '/mavros/setpoint_position/local', 10)
        
        # Wait for services
        while not self.arm_srv.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for arming service...')
    
    def state_cb(self, msg):
        self.state = msg
    
    def set_mode(self, mode):
        req = SetMode.Request()
        req.custom_mode = mode
        future = self.mode_srv.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result().success
    
    def arm(self):
        req = CommandBool.Request()
        req.value = True
        future = self.arm_srv.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result().success
    
    def send_setpoint(self, x, y, z):
        sp = PoseStamped()
        sp.pose.position.x = x
        sp.pose.position.y = y
        sp.pose.position.z = z
        sp.pose.orientation.w = 1.0  # Identity quaternion
        self.sp_pub.publish(sp)
    
    def test_sequence(self):
        self.get_logger().info("=== ARMING & TAKEOFF TEST ===")
        
        # Wait for connection
        for i in range(30):
            if self.state and self.state.connected:
                break
            time.sleep(0.5)
        
        if not self.state or not self.state.connected:
            self.get_logger().error("Not connected!")
            return
        
        self.get_logger().info(f"Connected! Current mode: {self.state.mode}")
        
        # Set to GUIDED
        self.get_logger().info("Setting mode to GUIDED...")
        if self.set_mode('GUIDED'):
            self.get_logger().info("Mode set to GUIDED ✓")
        else:
            self.get_logger().error("Failed to set mode!")
            return
        
        time.sleep(1)
        
        # Arm
        self.get_logger().info("Arming...")
        if self.arm():
            self.get_logger().info("Armed ✓")
        else:
            self.get_logger().error("Failed to arm!")
            return
        
        time.sleep(1)
        
        # Send takeoff setpoint (1 meter up)
        self.get_logger().info("Sending takeoff command (1m altitude)...")
        for i in range(30):
            self.send_setpoint(0, 0, 1.0)
            time.sleep(0.1)
        
        time.sleep(5)
        self.get_logger().info("Test complete!")

def main():
    rclpy.init()
    controller = DroneController()
    try:
        controller.test_sequence()
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## Part 8: Next Steps

1. **Run verification sequence** in the order above
2. **Check monitor output** for heartbeat first
3. **Verify IMU/position data** once heartbeat confirmed
4. **Test arming/mode commands** on tethered/secured drone
5. **Integrate with your autonomous code** (SUPER, DarkNet3D, etc.)

**Safety:** Always keep props off, drone tethered, and FC on bench during initial testing!
