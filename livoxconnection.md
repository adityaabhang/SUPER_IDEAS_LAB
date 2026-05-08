# Livox MID-360 — Full Session Log
## Connection, FAST-LIO2, SUPER Planner & Hybrid Simulation

**Hardware:** Jetson Orin Nano (ROS2 Humble) + Livox MID-360 via Ethernet

---

## What Was Built (End State)

| Component | Location | Status |
|-----------|----------|--------|
| Livox ROS2 driver | `/home/ideas-ad/ws_livox` | Built, working |
| FAST-LIO2 (ROS2 branch) | `/home/ideas-ad/super_ws/src/FAST_LIO_ROS2` | Built, working |
| SUPER planner | `/home/ideas-ad/super_ws/src/SUPER/super_planner` | Working |
| Hybrid sim launch | `/home/ideas-ad/super_ws/src/SUPER/mission_planner/launch/real_lidar_sim.launch.py` | Working |
| RViz config | `/home/ideas-ad/livox_view.rviz` | Full pipeline view |

---

## One-Time Setup (Already Done)

### 1. Ethernet — Jetson interface is `enP8p1s0`, NOT `eth0`

The guide uses `eth0` but the Jetson Orin Nano uses predictable names.
Check with: `ip link show`

Assign IP temporarily (resets on reboot):
```bash
sudo ip addr add 192.168.1.50/24 dev enP8p1s0
sudo ip link set enP8p1s0 up
```

Make permanent via netplan:
```bash
sudo bash -c 'cat > /etc/netplan/02-livox.yaml << EOF
network:
  version: 2
  ethernets:
    enP8p1s0:
      addresses: [192.168.1.50/24]
      dhcp4: false
EOF'
sudo netplan apply
```

Verify:
```bash
ip addr show enP8p1s0   # must show: inet 192.168.1.50/24
ping -c 3 192.168.1.154 # must show: 0% packet loss
```

> **Note:** `sudo ip addr add` requires an interactive desktop terminal — it cannot be run via Claude Code (no password prompt). Open a terminal on the Jetson desktop.

---

### 2. Fix ws_livox build conflict

A leftover directory blocked `--symlink-install`. Fix and rebuild:
```bash
rm -rf /home/ideas-ad/ws_livox/build/livox_ros_driver2/ament_cmake_python/livox_ros_driver2/livox_ros_driver2

source /opt/ros/humble/setup.bash
cd /home/ideas-ad/ws_livox
colcon build --symlink-install
# Expected: Summary: 1 packages finished
```

---

### 3. xfer_format — must be 1 (CustomMsg) for FAST-LIO2

**Issue found and corrected:** The nohardware.md guide said to set `xfer_format = 0` (PointCloud2). This was wrong. FAST-LIO2 with `lidar_type: 1` subscribes to `livox_ros_driver2/msg/CustomMsg`, not `sensor_msgs/msg/PointCloud2`. With mismatched types, no data flows.

**Correct setting:** `xfer_format = 1`

File: `/home/ideas-ad/ws_livox/src/livox_ros_driver2/launch_ROS2/msg_MID360_launch.py`
```python
xfer_format   = 1    # 1 = CustomMsg (required for FAST-LIO2 lidar_type: 1)
```

Verify:
```bash
grep "xfer_format" /home/ideas-ad/ws_livox/src/livox_ros_driver2/launch_ROS2/msg_MID360_launch.py
# Expected: xfer_format   = 1
```

---

### 4. Install FAST-LIO2 (ROS2 branch)

**Note:** FAST-LIVO2 was considered but rejected — it is ROS1 only (catkin) and requires a camera. Used `FAST_LIO` ROS2 branch instead.

```bash
cd /home/ideas-ad/super_ws/src
git clone https://github.com/hku-mars/FAST_LIO.git FAST_LIO_ROS2 --branch ROS2 --depth 1

# Init submodule (ikd-Tree — not included in --depth 1 clone)
cd FAST_LIO_ROS2
git submodule update --init --recursive

# Build
source /opt/ros/humble/setup.bash
source /home/ideas-ad/ws_livox/install/setup.bash
cd /home/ideas-ad/super_ws
colcon build --symlink-install --packages-select fast_lio
# Expected: Summary: 1 packages finished
```

**Issues hit during build:**
- First build failed: stale CMake cache from a previous path → `rm -rf build/fast_lio install/fast_lio` then rebuild
- Second build failed: `ikd_Tree.cpp` not found → submodule was empty because `--depth 1` skips submodules → fixed with `git submodule update --init --recursive`

---

### 5. Topic remap in FAST-LIO2 launch file

SUPER expects `/lidar_slam/odom` but FAST-LIO2 publishes `/Odometry`.
Remap added to `/home/ideas-ad/super_ws/src/FAST_LIO_ROS2/launch/mapping.launch.py`:

```python
fast_lio_node = Node(
    package='fast_lio',
    executable='fastlio_mapping',
    parameters=[...],
    remappings=[('/Odometry', '/lidar_slam/odom')],  # added
    output='screen'
)
```

---

### 6. Dense point cloud settings in FAST-LIO2

Default settings produced a sparse `/cloud_registered`. Changed in
`/home/ideas-ad/super_ws/src/FAST_LIO_ROS2/config/mid360.yaml`:

| Parameter | Before | After | Effect |
|-----------|--------|-------|--------|
| `point_filter_num` | 3 | 1 | Keep every point (not every 3rd) |
| `filter_size_surf` | 0.5 | 0.2 | Finer voxel grid |
| `dense_publish_en` | false | true | Publish full scan, not downsampled map cloud |

---

### 7. SUPER planner virtual_ground_height fix

The drone sits at z ≈ 0. The ROG-Map's effective ground (after inflation) was 0.25 m, causing constant `Odom below virtual ground` warnings and map rejection.

Changed in `/home/ideas-ad/super_ws/src/SUPER/super_planner/config/static_dense.yaml`:
```yaml
virtual_ground_height: -1.0   # was -0.1
```

---

### 8. Hybrid simulation launch file

Created `/home/ideas-ad/super_ws/src/SUPER/mission_planner/launch/real_lidar_sim.launch.py`

**What it does:**
- Uses **real Livox LiDAR** (via FAST-LIO2) as the occupancy map
- Uses **perfect_drone_sim** (SUPER's built-in simulator) for virtual drone dynamics
- Connects them cleanly via topic remaps so they don't conflict

**Topic routing:**
| Topic | Source | Used by |
|-------|--------|---------|
| `/cloud_registered` | FAST-LIO2 (real) | SUPER planner map |
| `/lidar_slam/odom` | perfect_drone_sim | SUPER planner drone position |
| `/lidar_slam/odom_real` | FAST-LIO2 | Info only, not used by planner |
| `/sim/cloud_registered` | perfect_drone_sim | Suppressed (real map used instead) |
| `/planning/pos_cmd` | SUPER planner | Commands virtual drone |

**Static TF:** `world → camera_init` (identity) links the sim frame to FAST-LIO2's frame so both appear in RViz together.

---

## Every Time — Full Hybrid Pipeline

### Step 1 — Check IP and Livox connection
```bash
ip addr show enP8p1s0        # must show inet 192.168.1.50/24
ping -c 3 192.168.1.154      # must show 0% packet loss
```

If IP missing: `sudo ip addr add 192.168.1.50/24 dev enP8p1s0` (run in desktop terminal)

### Step 2 — Start Livox driver (Terminal 1)
```bash
source /opt/ros/humble/setup.bash
source /home/ideas-ad/ws_livox/install/setup.bash
ros2 launch livox_ros_driver2 msg_MID360_launch.py
```
Wait for: `livox/lidar publish use livox custom format`

### Step 3 — Launch full hybrid stack (Terminal 2)
```bash
source /opt/ros/humble/setup.bash
source /home/ideas-ad/ws_livox/install/setup.bash
source /home/ideas-ad/super_ws/install/setup.bash
ros2 launch mission_planner real_lidar_sim.launch.py
```

RViz opens automatically. Wait ~30 seconds for the FSM to transition from `INIT` → `WAIT_GOAL` (map needs to build up).

### Step 4 — Send a goal
In RViz: click **"2D Goal Pose"** in the toolbar, then click a point in the point cloud ~3–5 m away.

The FSM will cycle: `WAIT_GOAL` → `GENERATE_TRAJ` → `FOLLOW_TRAJ` → `WAIT_GOAL`

Verify trajectory is executing:
```bash
source /opt/ros/humble/setup.bash
source /home/ideas-ad/super_ws/install/setup.bash
ros2 topic hz /planning/pos_cmd   # ~100 Hz while flying
```

### Step 5 — Reset and fly again
Kill all nodes and relaunch:
```bash
kill -9 $(pgrep -f "fastlio_mapping|perfect_drone_node|fsm_node|rviz2")
# Then repeat Steps 2–4
```

---

## Key Facts

| Item | Value |
|------|-------|
| Jetson Ethernet interface | `enP8p1s0` (not `eth0`) |
| Jetson IP | `192.168.1.50/24` |
| Livox MID-360 IP | `192.168.1.154` |
| LiDAR ROS frame | `livox_frame` (raw) / `camera_init` (FAST-LIO2) |
| Sim drone frame | `world` |
| TF link | `world → camera_init` (identity, static) |
| xfer_format | `1` (CustomMsg — required for FAST-LIO2 lidar_type:1) |
| FAST-LIO2 odom topic (normal) | `/lidar_slam/odom` |
| FAST-LIO2 odom topic (hybrid) | `/lidar_slam/odom_real` |
| RViz config | `/home/ideas-ad/livox_view.rviz` |
| Hybrid launch file | `ros2 launch mission_planner real_lidar_sim.launch.py` |

---

## All Issues Encountered & Fixes

| # | Issue | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `cannot find device "eth0"` | Jetson uses predictable interface names | Use `enP8p1s0` |
| 2 | `ping` fails after IP assigned | `sudo ip addr add` wasn't run (needs desktop terminal) | Run in Jetson desktop terminal, not via Claude |
| 3 | `librclcpp.so: cannot open shared object file` | ws_livox build conflict (leftover directory blocked symlink) | `rm -rf` the conflicting dir, rebuild |
| 4 | FAST-LIO2 first build: CMake cache mismatch | Previous build used a different source path | `rm -rf build/fast_lio install/fast_lio`, rebuild |
| 5 | FAST-LIO2 second build: `ikd_Tree.cpp` not found | `--depth 1` clone doesn't pull submodules | `git submodule update --init --recursive` |
| 6 | FAST-LIO2 receives no LiDAR data | `xfer_format=0` publishes PointCloud2 but `lidar_type=1` subscribes to CustomMsg — type mismatch | Change `xfer_format` back to `1` |
| 7 | Point cloud sparse in hybrid sim | `dense_publish_en: false`, `point_filter_num: 3`, `filter_size_surf: 0.5` | Enable dense publish, set filter_num=1, filter_size=0.2 |
| 8 | `Odom below virtual ground` warning, map rejected | Drone at z≈0, virtual_ground_height effective value was +0.25 m | Set `virtual_ground_height: -1.0` in static_dense.yaml |
| 9 | FAST-LIVO2 rejected (user request) | ROS1 only (catkin), requires camera hardware | Switched to FAST_LIO ROS2 branch |
| 10 | Duplicate node instances after restarts | `pkill` exit code 144 (some processes not found) left old nodes running | Use `kill -9 $(pgrep -f ...)` for reliable cleanup |
| 11 | FSM stuck in INIT for ~30s | Normal — ROG-Map needs time to build up enough voxels | Wait for `WAIT_GOAL` before sending goal |
| 12 | Goal sent during INIT was ignored | FSM discards goals received before map is ready | Resend goal after FSM reaches `WAIT_GOAL` |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No `inet` on `enP8p1s0` | `sudo ip addr add 192.168.1.50/24 dev enP8p1s0` in desktop terminal |
| Ping to 192.168.1.154 fails | Check Livox is powered on and Ethernet cable is connected |
| `livox/lidar` not publishing | Restart Livox driver; check xfer_format=1 |
| FAST-LIO2 receives no data | Verify `xfer_format=1` and `lidar_type=1` in mid360.yaml |
| Point cloud is sparse | Check `dense_publish_en: true`, `point_filter_num: 1` in mid360.yaml |
| FSM stays in INIT forever | Check `/lidar_slam/odom` and `/cloud_registered` are both publishing |
| FSM in WAIT_GOAL, goal ignored | Goal sent too early (during INIT) — resend after WAIT_GOAL |
| Duplicate nodes running | `kill -9 $(pgrep -f "fastlio_mapping\|perfect_drone_node\|fsm_node\|rviz2")` |
| RViz shows no point cloud | Press `F` to reset camera; check Fixed Frame is `world` |
