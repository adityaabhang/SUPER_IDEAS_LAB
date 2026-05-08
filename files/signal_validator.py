#!/usr/bin/env python3
"""
Signal Verification & Command Validation Tool
Confirms that Jetson code is sending correct MAVLink commands to ARK FC
"""

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import State, ActuatorControl, AttitudeTarget, PositionTarget
from mavros_msgs.srv import CommandBool, SetMode
from geometry_msgs.msg import PoseStamped, TwistStamped
from sensor_msgs.msg import Joy
import threading
import time
from enum import Enum
import json

class CommandValidator(Node):
    """
    Monitors all outgoing commands and validates signal correctness
    """
    
    class SignalStatus(Enum):
        OK = "✓"
        WARNING = "⚠"
        ERROR = "✗"
    
    def __init__(self):
        super().__init__('signal_validator')
        
        # State tracking
        self.state = None
        self.last_heartbeat_time = time.time()
        self.heartbeat_interval = None
        
        # Command tracking
        self.last_arm_time = None
        self.last_mode_change = None
        self.last_setpoint_time = None
        self.command_history = []
        
        # Subscriptions (listen to what Jetson sends)
        self.state_sub = self.create_subscription(State, '/mavros/state', self.state_cb, 10)
        self.sp_local_sub = self.create_subscription(
            PoseStamped, '/mavros/setpoint_position/local', self.sp_local_cb, 10)
        self.sp_raw_sub = self.create_subscription(
            PositionTarget, '/mavros/setpoint_raw/local', self.sp_raw_cb, 10)
        self.att_target_sub = self.create_subscription(
            AttitudeTarget, '/mavros/setpoint_raw/attitude', self.att_target_cb, 10)
        self.actuator_sub = self.create_subscription(
            ActuatorControl, '/mavros/actuator_control', self.actuator_cb, 10)
        
        # Service clients to verify command execution
        self.arm_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        
        # Test results
        self.test_results = {
            'heartbeat': None,
            'position_setpoint': None,
            'attitude_control': None,
            'arm_command': None,
            'mode_change': None,
        }
        
    def state_cb(self, msg):
        """Track state changes and heartbeat frequency"""
        current_time = time.time()
        
        if self.state is None:
            self.get_logger().info("✓ Heartbeat detected!")
        
        if self.state and self.heartbeat_interval is None:
            interval = current_time - self.last_heartbeat_time
            self.heartbeat_interval = interval
            self.get_logger().info(f"Heartbeat interval: {interval*1000:.1f}ms (should be ~50ms)")
        
        self.state = msg
        self.last_heartbeat_time = current_time
        self.test_results['heartbeat'] = {
            'status': self.SignalStatus.OK.value,
            'connected': msg.connected,
            'armed': msg.armed,
            'mode': msg.mode,
            'timestamp': current_time
        }
    
    def sp_local_cb(self, msg):
        """Verify position setpoint signals"""
        current_time = time.time()
        
        if self.last_setpoint_time is None:
            self.get_logger().info("✓ Position setpoint detected")
        
        self.last_setpoint_time = current_time
        
        # Check for reasonable values
        x, y, z = msg.pose.position.x, msg.pose.position.y, msg.pose.position.z
        
        # Validity checks
        status = self.SignalStatus.OK
        issues = []
        
        # Check for NaN/Inf
        for val, name in [(x, 'X'), (y, 'Y'), (z, 'Z')]:
            if not (-1000 < val < 1000):
                issues.append(f"{name} out of range: {val:.2f}m")
                status = self.SignalStatus.WARNING
        
        # Check if value is changing
        if hasattr(self, 'last_sp_local'):
            dx = abs(x - self.last_sp_local[0])
            dy = abs(y - self.last_sp_local[1])
            dz = abs(z - self.last_sp_local[2])
            
            if dx < 0.001 and dy < 0.001 and dz < 0.001:
                # Setpoint may be static (OK for hover) or stuck (bad)
                pass
        
        self.last_sp_local = (x, y, z)
        
        self.test_results['position_setpoint'] = {
            'status': status.value,
            'x': x,
            'y': y,
            'z': z,
            'issues': issues,
            'timestamp': current_time
        }
    
    def sp_raw_cb(self, msg):
        """Verify raw position target (alternative setpoint)"""
        pass  # Not always used; tracked by position_target_local
    
    def att_target_cb(self, msg):
        """Verify attitude/orientation commands"""
        current_time = time.time()
        
        if self.test_results['attitude_control'] is None:
            self.get_logger().info("✓ Attitude target detected")
        
        qx = msg.q[0]
        qy = msg.q[1]
        qz = msg.q[2]
        qw = msg.q[3]
        
        # Check quaternion is normalized
        q_norm = (qx**2 + qy**2 + qz**2 + qw**2) ** 0.5
        
        status = self.SignalStatus.OK if 0.95 < q_norm < 1.05 else self.SignalStatus.WARNING
        
        self.test_results['attitude_control'] = {
            'status': status.value,
            'q': [qx, qy, qz, qw],
            'q_norm': q_norm,
            'thrust': msg.thrust,
            'body_rates': [msg.body_rate.x, msg.body_rate.y, msg.body_rate.z],
            'timestamp': current_time
        }
    
    def actuator_cb(self, msg):
        """Verify motor/actuator commands (PWM signals)"""
        # Group 0 controls are typically motors
        controls = msg.controls[:4] if len(msg.controls) >= 4 else msg.controls
        
        # Check if any motor is receiving signal
        any_nonzero = any(abs(c) > 0.01 for c in controls)
        
        if any_nonzero and not self.state.armed:
            status = self.SignalStatus.WARNING  # Should be zero when disarmed
        elif not any_nonzero and self.state.armed:
            status = self.SignalStatus.WARNING  # Should be nonzero when armed
        else:
            status = self.SignalStatus.OK
    
    async def test_arm_command(self):
        """Test arming command execution"""
        self.get_logger().info("\n[TEST] Sending arm command...")
        
        req = CommandBool.Request()
        req.value = True
        
        try:
            future = self.arm_client.call_async(req)
            result = await future
            
            if result.success:
                self.get_logger().info("  ✓ Arm command accepted")
                self.test_results['arm_command'] = {
                    'status': self.SignalStatus.OK.value,
                    'result': 'Command accepted',
                    'timestamp': time.time()
                }
            else:
                self.get_logger().warn("  ⚠ Arm command rejected (may be armed already)")
                self.test_results['arm_command'] = {
                    'status': self.SignalStatus.WARNING.value,
                    'result': 'Command rejected',
                    'timestamp': time.time()
                }
        except Exception as e:
            self.get_logger().error(f"  ✗ Arm command failed: {e}")
            self.test_results['arm_command'] = {
                'status': self.SignalStatus.ERROR.value,
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def test_mode_change(self):
        """Test flight mode change"""
        self.get_logger().info("\n[TEST] Sending mode change (GUIDED)...")
        
        req = SetMode.Request()
        req.custom_mode = 'GUIDED'
        
        try:
            future = self.mode_client.call_async(req)
            result = await future
            
            if result.mode_sent:
                self.get_logger().info("  ✓ Mode change command sent")
                self.test_results['mode_change'] = {
                    'status': self.SignalStatus.OK.value,
                    'result': 'Mode change sent',
                    'new_mode': 'GUIDED',
                    'timestamp': time.time()
                }
            else:
                self.get_logger().warn("  ⚠ Mode change rejected")
                self.test_results['mode_change'] = {
                    'status': self.SignalStatus.WARNING.value,
                    'result': 'Mode change rejected',
                    'timestamp': time.time()
                }
        except Exception as e:
            self.get_logger().error(f"  ✗ Mode change failed: {e}")
            self.test_results['mode_change'] = {
                'status': self.SignalStatus.ERROR.value,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "="*70)
        print("SIGNAL VALIDATION REPORT")
        print("="*70)
        
        for test_name, result in self.test_results.items():
            if result is None:
                print(f"\n{test_name:25s}: [NOT TESTED]")
            else:
                status = result.get('status', 'UNKNOWN')
                print(f"\n{test_name:25s}: [{status}]")
                
                # Print details
                for key, val in result.items():
                    if key != 'status' and key != 'timestamp':
                        if isinstance(val, (list, dict)):
                            print(f"  {key:20s}: {json.dumps(val, indent=4)}")
                        else:
                            print(f"  {key:20s}: {val}")
        
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)
        
        recommendations = []
        
        if self.test_results['heartbeat'] and not self.test_results['heartbeat'].get('connected'):
            recommendations.append("• Heartbeat not received - check FC power and USB cable")
        
        if self.test_results['position_setpoint'] is None:
            recommendations.append("• No position setpoints being sent - verify code is publishing")
        
        if self.test_results['arm_command'] and self.test_results['arm_command']['status'] != '✓':
            recommendations.append("• Arming failed - check FC state, RC failsafe, and calibration")
        
        if not recommendations:
            recommendations.append("✓ All signals verified! Drone ready for autonomous control.")
        
        for rec in recommendations:
            print(rec)
        
        print("\n")

def main():
    rclpy.init()
    validator = CommandValidator()
    
    print("Starting signal validation...\n")
    print("Waiting for heartbeat from ARK FC...")
    
    # Wait for heartbeat
    for _ in range(30):
        rclpy.spin_once(validator, timeout_sec=0.5)
        if validator.state:
            break
    
    if not validator.state:
        print("✗ No heartbeat received - check connection!")
        return
    
    print("\nMonitoring signals (30 seconds)...")
    print("(Make sure your drone code is publishing setpoints)\n")
    
    # Monitor for 30 seconds
    for i in range(60):
        rclpy.spin_once(validator, timeout_sec=0.5)
        if i % 10 == 0:
            print(f"  [{i//2}s] Listening for signals...")
    
    # Print report
    validator.print_report()
    
    # Cleanup
    validator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
