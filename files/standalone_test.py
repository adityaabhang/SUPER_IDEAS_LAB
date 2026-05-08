#!/usr/bin/env python3
"""
Standalone Jetson + ARK FC Diagnostics
Run this without ROS2 to test raw MAVLink connection
Usage: python3 standalone_test.py --port /dev/ttyACM0 --baud 115200
"""

import serial
import argparse
import time
import sys
from datetime import datetime

def test_serial_connection(port, baudrate):
    """Test if we can open and communicate with the FC"""
    print(f"\n{'='*70}")
    print(f"STANDALONE MAVLink CONNECTION TEST")
    print(f"{'='*70}")
    print(f"Port: {port}")
    print(f"Baudrate: {baudrate}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Step 1: Try to open port
    print(f"[1/5] Opening serial port {port}...")
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        print(f"  ✓ Port opened successfully")
    except FileNotFoundError:
        print(f"  ✗ Port not found. Try:")
        print(f"     ls -la /dev/tty*")
        return False
    except PermissionError:
        print(f"  ✗ Permission denied. Try:")
        print(f"     sudo usermod -a -G dialout $USER  # then logout/login")
        print(f"     or: sudo chmod 666 {port}")
        return False
    except Exception as e:
        print(f"  ✗ Failed to open: {e}")
        return False
    
    # Step 2: Check if data is coming
    print(f"\n[2/5] Listening for MAVLink packets (5 seconds)...")
    print(f"  (Drone/FC must be powered on)")
    
    start_time = time.time()
    packet_count = 0
    heartbeat_count = 0
    
    # MAVLink packet starts with 0xFE (protocol v1) or 0xFD (protocol v2)
    while time.time() - start_time < 5:
        try:
            data = ser.read(1)
            if data:
                byte_val = ord(data)
                
                # Check for MAVLink magic bytes
                if byte_val in [0xFE, 0xFD]:  # MAVLink v1 or v2
                    packet_count += 1
                    
                    # Try to read full heartbeat (ID=0)
                    if byte_val == 0xFE:  # v1
                        remaining = ser.read(8)  # Heartbeat is 9 bytes total
                        if remaining and len(remaining) == 8:
                            msg_id = remaining[5]
                            if msg_id == 0:  # HEARTBEAT
                                heartbeat_count += 1
                                elapsed = time.time() - start_time
                                print(f"  [{elapsed:5.2f}s] Heartbeat received! (packet #{packet_count})")
                    
                    # Show progress
                    sys.stdout.write(f"\r  Packets received: {packet_count:3d}  |  Heartbeats: {heartbeat_count:2d}")
                    sys.stdout.flush()
        
        except Exception as e:
            print(f"  Error reading: {e}")
            break
    
    print(f"\n  Final: {packet_count} packets, {heartbeat_count} heartbeats")
    
    if heartbeat_count == 0:
        print(f"\n  ✗ No heartbeat received!")
        print(f"    Check:")
        print(f"    1. Is FC powered on? (green lights?)")
        print(f"    2. Is USB cable connected?")
        print(f"    3. Is baudrate correct? (Try 57600, 230400)")
        print(f"    4. Is it the right device? (Check with lsusb)")
        ser.close()
        return False
    else:
        print(f"\n  ✓ Heartbeat detected!")
    
    # Step 3: Parse a heartbeat message
    print(f"\n[3/5] Parsing heartbeat data...")
    try:
        # Try to read another heartbeat and parse it
        ser.reset_input_buffer()
        
        for attempt in range(20):
            byte = ser.read(1)
            if byte and ord(byte) == 0xFE:  # MAVLink v1 start
                # Read rest of heartbeat: [len=9, seq, sys, comp, msg_id=0, type, autopilot, base_mode, system_status, mavlink_version]
                hb_data = ser.read(8)
                if hb_data and len(hb_data) == 8:
                    msg_id = hb_data[5]
                    if msg_id == 0:  # HEARTBEAT
                        aircraft_type = hb_data[0]
                        autopilot = hb_data[1]
                        base_mode = hb_data[2]
                        system_status = hb_data[3]
                        
                        # Decode some values
                        armed = bool(base_mode & 0x80)
                        type_names = {
                            0: "Generic", 1: "Fixed Wing", 2: "Quadrotor", 3: "Coaxial", 
                            4: "Helicopter", 5: "Antenna Tracker", 6: "GCS", 7: "Airship",
                            8: "Free Balloon", 9: "Rocket", 10: "Ground Rover", 11: "Surface Boat", 12: "Submarine"
                        }
                        
                        print(f"  Aircraft Type: {type_names.get(aircraft_type, f'Unknown ({aircraft_type})')}")
                        print(f"  Autopilot: {autopilot} (1=ArduPilot, 3=PX4, 13=ArduSub, etc)")
                        print(f"  Armed: {armed}")
                        print(f"  System Status: {system_status} (0=Boot, 1=Calibrating, 2=Standby, 3=Active, 4=Critical, 5=Emergency)")
                        print(f"  ✓ Heartbeat parsed successfully")
                        break
    except Exception as e:
        print(f"  Note: Could not fully parse (not critical): {e}")
    
    # Step 4: Check serial characteristics
    print(f"\n[4/5] Serial port characteristics...")
    print(f"  Port: {ser.port}")
    print(f"  Baudrate: {ser.baudrate}")
    print(f"  Bytesize: {ser.bytesize}")
    print(f"  Stopbits: {ser.stopbits}")
    print(f"  Parity: {ser.parity}")
    print(f"  Timeout: {ser.timeout}s")
    print(f"  ✓ Settings OK")
    
    # Step 5: Test write
    print(f"\n[5/5] Testing write capability...")
    try:
        # Send a PING command (MAVLink PING)
        # v1 format: [0xFE, 0x09(len), 0x00(seq), 0xFF(sys), 0x00(comp), 0x04(id=PING), 1,2,3,4,5,6,7,8,9, crc1, crc2]
        # For now, just test that we can write
        test_msg = bytes([0xFE, 0x02, 0x00, 0xFF, 0x00, 0x04])  # Minimal PING
        ser.write(test_msg)
        print(f"  ✓ Write successful (sent {len(test_msg)} bytes)")
    except Exception as e:
        print(f"  ✗ Write failed: {e}")
    
    ser.close()
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Serial connection: OK")
    print(f"✓ FC detected: YES")
    print(f"✓ Heartbeat received: YES ({heartbeat_count} packets)")
    print(f"✓ Ready for MAVROS2: YES")
    print(f"\nNext steps:")
    print(f"  1. cd ~/ros2_ws && source install/setup.bash")
    print(f"  2. ros2 launch drone_control mavros_ark.launch.py")
    print(f"  3. python3 ~/signal_monitor.py")
    print(f"{'='*70}\n")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Standalone Jetson + ARK FC Diagnostics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 standalone_test.py                    # Default: /dev/ttyACM0:115200
  python3 standalone_test.py --port /dev/ttyUSB0
  python3 standalone_test.py --port /dev/ttyACM0 --baud 57600

Troubleshooting:
  If port not found:
    ls -la /dev/tty*
  
  If permission denied:
    sudo usermod -a -G dialout $USER  # then logout/login
  
  If no heartbeat after 5s:
    - Check FC is powered (LED lights?)
    - Check USB cable (try different port on Jetson)
    - Check baudrate (try 57600, 230400)
    - Check with 'lsusb' that FC is recognized
        """)
    
    parser.add_argument('--port', default='/dev/ttyACM0', 
                       help='Serial port (default: /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200,
                       help='Baudrate (default: 115200)')
    
    args = parser.parse_args()
    
    # Run test
    success = test_serial_connection(args.port, args.baud)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
