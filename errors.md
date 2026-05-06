ideas-ad@ideasad-desktop:~/super_ws$ colcon build --symlink-install
Starting >>> mars_quadrotor_msgs
Starting >>> marsim_render
Starting >>> rog_map
Starting >>> mission_planner
[Processing: mars_quadrotor_msgs, marsim_render, mission_planner, rog_map]     
Finished <<< mars_quadrotor_msgs [36.3s]                                    
[Processing: marsim_render, mission_planner, rog_map]                       
[Processing: marsim_render, mission_planner, rog_map]
--- stderr: marsim_render                                                      
CMake Warning (dev) at /usr/share/cmake-3.22/Modules/FindOpenGL.cmake:315 (message):
  Policy CMP0072 is not set: FindOpenGL prefers GLVND by default when
  available.  Run "cmake --help-policy CMP0072" for policy details.  Use the
  cmake_policy command to set the policy and suppress this warning.

  FindOpenGL found both a legacy GL library:

    OPENGL_gl_LIBRARY: /usr/lib/aarch64-linux-gnu/libGL.so

  and GLVND libraries for OpenGL and GLX:

    OPENGL_opengl_LIBRARY: /usr/lib/aarch64-linux-gnu/libOpenGL.so
    OPENGL_glx_LIBRARY: /usr/lib/aarch64-linux-gnu/libGLX.so

  OpenGL_GL_PREFERENCE has not been set to "GLVND" or "LEGACY", so for
  compatibility with CMake 3.10 and below the legacy GL library will be used.
Call Stack (most recent call first):
  CMakeLists.txt:48 (find_package)
This warning is for project developers.  Use -Wno-dev to suppress it.

** WARNING ** io features related to pcap will be disabled
cc1: warning: command-line option ‘-Wnon-virtual-dtor’ is valid for C++/ObjC++ but not for C
cc1: warning: command-line option ‘-Woverloaded-virtual’ is valid for C++/ObjC++ but not for C
---
Finished <<< marsim_render [2min 4s]
Starting >>> perfect_drone_sim
--- stderr: perfect_drone_sim                                               
** WARNING ** io features related to pcap will be disabled
In file included from /home/ideas-ad/super_ws/src/SUPER/mars_uav_sim/perfect_drone_sim/src/ros2_perfect_drone_node.cpp:1:
/home/ideas-ad/super_ws/src/SUPER/mars_uav_sim/perfect_drone_sim/include/perfect_drone_sim/ros2_perfect_drone_model.hpp:14:10: fatal error: pcl_conversions/pcl_conversions.h: No such file or directory
   14 | #include "pcl_conversions/pcl_conversions.h"
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
compilation terminated.
gmake[2]: *** [CMakeFiles/perfect_drone_node.dir/build.make:76: CMakeFiles/perfect_drone_node.dir/src/ros2_perfect_drone_node.cpp.o] Error 1
gmake[1]: *** [CMakeFiles/Makefile2:137: CMakeFiles/perfect_drone_node.dir/all] Error 2
gmake: *** [Makefile:146: all] Error 2
---
Failed   <<< perfect_drone_sim [13.8s, exited with code 2]
Aborted  <<< mission_planner [2min 59s]               
Aborted  <<< rog_map [3min 5s]                                         

Summary: 2 packages finished [3min 6s]
  1 package failed: perfect_drone_sim
  2 packages aborted: mission_planner rog_map
  4 packages had stderr output: marsim_render mission_planner perfect_drone_sim rog_map
  1 package not processed
