# FishROS2 URDF 学习代码（Gazebo Harmonic 适配版）

## 1. 项目介绍

本仓库是学习 FishROS ROS 2 课程第六章 URDF、Xacro、RViz 和 Gazebo
过程中整理的代码。

原教程使用的系统和 Gazebo 版本与本项目不同，教程中的部分
Gazebo Classic 插件不能直接用于 Gazebo Harmonic。本项目完成了以下迁移：

- 使用 `ros_gz_sim` 启动 Gazebo Harmonic；
- 使用 `ros_gz_sim create` 生成机器人；
- 使用 Gazebo Harmonic 原生雷达、IMU 和 RGB-D 相机；
- 使用 `ros_gz_bridge` 桥接传感器话题；
- 使用 `gz_ros2_control` 和 `diff_drive_controller` 控制小车；
- 将旧版 Gazebo world、模型资源和纹理路径适配到 Harmonic。

当前开发环境：

- Ubuntu 24.04；
- ROS 2 Jazzy；
- Gazebo Harmonic（Gazebo Sim 8）。

> 本文中的“旧版 Gazebo”或“Gazebo Classic”主要指教程中使用的
> Gazebo Classic；“Harmonic”指新版 Gazebo Sim。

## 2. 项目结构

```text
chapt6_ws/
└── src/
    ├── README.md
    └── fishbot_description/
        ├── config/
        │   ├── display_robot_model.rviz
        │   └── fishbot_ros2_controller.yaml
        ├── launch/
        │   ├── display_robot.launch.py
        │   └── gazebo_sim_launch.py
        ├── urdf/
        │   ├── first_robot.urdf
        │   ├── first_robot.xacro
        │   └── fishbot/
        │       ├── actuator/
        │       ├── plugins/
        │       ├── sensor/
        │       ├── base.urdf.xacro
        │       ├── fishbot.ros2_control.xacro
        │       └── fishbot.urdf.xacro
        └── world/
            ├── custom_room.world
            └── room/
                ├── model.config
                └── model.sdf
```

几个容易混淆的文件：

- `fishbot.urdf.xacro`：机器人的总装文件；
- `fishbot.ros2_control.xacro`：声明左右轮的控制接口并加载
  `gz_ros2_control`；
- `fishbot_ros2_controller.yaml`：选择并配置官方差速控制器；
- `gazebo_sensor_plugin.xacro`：配置雷达、IMU 和 RGB-D 相机；
- `gazebo_sim_launch.py`：启动 Gazebo、生成机器人、桥接传感器并启动控制器；
- `custom_room.world`：Gazebo 仿真世界。

## 3. 安装依赖

### 3.1 安装 ROS 2、Gazebo 与桥接组件

确保 ROS 2 Jazzy 已经安装，然后执行：

```bash
sudo apt update
sudo apt install \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-rviz2
```

### 3.2 安装 ros2_control

```bash
sudo apt install \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-gz-ros2-control
```

可选安装键盘控制工具：

```bash
sudo apt install \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-rqt-image-view \
  ros-jazzy-tf2-tools
```

注意：

- Harmonic 使用 `gz_ros2_control`；
- 不要使用 Gazebo Classic 的 `gazebo_ros2_control`；
- 不要加载 `libgazebo_ros2_control.so`。

## 4. 构建与运行

### 4.1 构建

```bash
cd ~/chapt6/chapt6_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select fishbot_description --symlink-install
source install/setup.bash
```

每次打开新终端都需要加载工作空间：

```bash
source /opt/ros/jazzy/setup.bash
source ~/chapt6/chapt6_ws/install/setup.bash
```

如果没有加载工作空间，会出现：

```text
Package 'fishbot_description' not found
```

可以使用下面的命令确认功能包已经被发现：

```bash
ros2 pkg prefix fishbot_description
```

正确结果应指向：

```text
~/chapt6/chapt6_ws/install/fishbot_description
```

### 4.2 在 RViz 中显示模型

```bash
ros2 launch fishbot_description display_robot.launch.py
```

RViz 配置文件只保存显示插件、Fixed Frame、颜色和视角等设置，并不保存
URDF 模型本身。RViz 中显示的机器人始终来自：

```text
/robot_description
TF
```

因此修改 Xacro 后重新构建并启动，仍然使用同一个 `.rviz` 配置文件也会显示
新模型，而不是旧模型。

### 4.3 启动 Gazebo Harmonic

```bash
ros2 launch fishbot_description gazebo_sim_launch.py
```

该 launch 文件会自动完成：

1. 使用 Xacro 生成 `robot_description`；
2. 启动 `robot_state_publisher`；
3. 启动 Gazebo Harmonic 和 `custom_room.world`；
4. 使用 `ros_gz_sim create` 生成 FishBot；
5. 启动传感器桥接；
6. 启动 `joint_state_broadcaster`；
7. 启动 `fishbot_diff_drive_controller`。

## 5. 控制小车

### 5.1 当前控制链

```text
ROS /cmd_vel (TwistStamped)
             ↓
fishbot_diff_drive_controller
             ↓
左右轮 velocity command interfaces
             ↓
controller_manager
             ↓
gz_ros2_control
             ↓
Gazebo 左右轮关节
```

这里各部分的作用是：

- `fishbot.ros2_control.xacro`：声明左右轮可以接收速度命令，并反馈位置和速度；
- `gz_ros2_control`：把 ros2_control 接口连接到 Gazebo 关节；
- `controller_manager`：加载、启动和管理控制器；
- `fishbot_diff_drive_controller`：官方差速控制器实例，把车体速度换算为左右轮速度；
- `joint_state_broadcaster`：发布 `/joint_states`。

`fishbot_diff_drive_controller` 只是本项目给控制器实例取的名字，真正加载的
控制器类型是：

```yaml
type: diff_drive_controller/DiffDriveController
```

### 5.2 检查控制器

```bash
ros2 control list_controllers
```

正常情况下应看到：

```text
joint_state_broadcaster        active
fishbot_diff_drive_controller  active
```

检查硬件接口：

```bash
ros2 control list_hardware_interfaces
```

正常情况下左右轮速度接口应显示：

```text
left_wheel_joint/velocity  [available] [claimed]
right_wheel_joint/velocity [available] [claimed]
```

`claimed` 不是报错。它表示活动的差速控制器已经取得轮子速度接口的控制权，
可以防止另一个控制器同时控制同一个关节。

下面两个接口显示 `unclaimed` 也是正常的：

```text
fishbot_diff_drive_controller/linear/velocity
fishbot_diff_drive_controller/angular/velocity
```

它们是控制器链式模式使用的参考接口；当前项目通过 `/cmd_vel` 控制，没有启用
链式控制器。

### 5.3 直接发送速度

Jazzy 的 `diff_drive_controller` 接收
`geometry_msgs/msg/TwistStamped`。

让小车以 `0.2 m/s` 前进：

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.2}, angular: {z: 0.0}}}"
```

原地左转：

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.0}, angular: {z: 0.5}}}"
```

停止：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}"
```

控制器配置了 `cmd_vel_timeout: 0.5`，停止发送命令约 0.5 秒后，小车也会自动
停止。

### 5.4 键盘控制（可选）

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true
```

常用按键：

- `i`：前进；
- `,`：后退；
- `j`：左转；
- `l`：右转；
- `k`：停止；
- `q/z`：增加或减小整体速度。

必须设置 `stamped:=true`，否则键盘节点发布的是 `Twist`，而 Jazzy
差速控制器需要 `TwistStamped`。

## 6. Gazebo Classic 与 Harmonic 的主要差异

| 功能 | Gazebo Classic | Gazebo Harmonic |
|---|---|---|
| 启动命令 | `gazebo` | `gz sim` |
| ROS 集成 | `gazebo_ros` | `ros_gz_sim` |
| 生成机器人 | `spawn_entity.py` | `ros_gz_sim create` |
| 通信 | 插件可直接使用 ROS | Gazebo Transport 与 ROS DDS 相互独立 |
| 桥接 | 通常不需要 | 使用 `ros_gz_bridge` |
| 差速插件 | `libgazebo_ros_diff_drive.so` | `gz-sim-diff-drive-system` 或 `gz_ros2_control` |
| ros2_control | `gazebo_ros2_control` | `gz_ros2_control` |
| GPU 雷达 | `ray` / GPU Ray | `gpu_lidar` |
| 模型路径 | `GAZEBO_MODEL_PATH` | `GZ_SIM_RESOURCE_PATH` |
| Building Editor | 提供完整编辑器 | 没有 Classic 同等完整的 Building Editor |

### 6.1 launch 与生成机器人

Classic 教程常用：

```bash
ros2 run gazebo_ros spawn_entity.py \
  -topic /robot_description \
  -entity fishbot
```

Harmonic 使用：

```bash
ros2 run ros_gz_sim create \
  -world default \
  -topic /robot_description \
  -name fishbot \
  -z 0.2
```

下面的命令不完整：

```bash
ros2 launch ros_gz_sim
```

`ros2 launch` 必须同时指定功能包和 launch 文件。查看包内可用 launch 文件：

```bash
ls /opt/ros/jazzy/share/ros_gz_sim/launch
```

直接启动 Gazebo Sim 的完整形式为：

```bash
ros2 launch ros_gz_sim gz_sim.launch.py
```

### 6.2 ROS 话题与 Gazebo Transport

Harmonic 中存在两套话题：

```bash
ros2 topic list
gz topic -l
```

前者是 ROS 2 DDS，后者是 Gazebo Transport。Gazebo 原生插件不会因为话题
名字相同就自动与 ROS 通信。

如果使用 Harmonic 原生 `gz-sim-diff-drive-system`，通常需要桥接
`/cmd_vel`、`/odom` 等话题。

本项目使用 `gz_ros2_control`，控制器本身运行在 ROS 2 中，因此以下控制话题
不需要桥接：

```text
/cmd_vel
/odom
/tf
/joint_states
```

雷达、IMU、相机属于 Gazebo 原生传感器，它们的话题仍然需要桥接。

### 6.3 不要加载两套差速控制

下面两个方案只能选择一个：

```text
gz-sim-diff-drive-system
```

或者：

```text
diff_drive_controller + gz_ros2_control
```

如果同时加载，它们会争抢左右轮。本项目保留了旧插件文件作为学习记录，但主
Xacro 不再引用 `gazebo_control_plugin.xacro`。

## 7. ros2_control 的 Harmonic 适配

Gazebo Classic 写法：

```xml
<hardware>
  <plugin>gazebo_ros2_control/GazeboSystem</plugin>
</hardware>

<plugin
  filename="libgazebo_ros2_control.so"
  name="gazebo_ros2_control"/>
```

Gazebo Harmonic 写法：

```xml
<hardware>
  <plugin>gz_ros2_control/GazeboSimSystem</plugin>
</hardware>

<plugin
  filename="libgz_ros2_control-system.so"
  name="gz_ros2_control::GazeboSimROS2ControlPlugin"/>
```

普通 URDF `<joint>` 只描述关节的结构、父子 link 和旋转轴。
`<ros2_control>` 则声明这个关节提供哪些控制和状态接口：

```xml
<joint name="left_wheel_joint">
  <command_interface name="velocity"/>
  <state_interface name="position"/>
  <state_interface name="velocity"/>
</joint>
```

含义为：

- 可以给左轮发送速度命令；
- 可以读取左轮位置；
- 可以读取左轮速度。

控制器由 YAML 声明类型，再由 launch 中的 `spawner` 请求
`controller_manager` 加载并激活。

## 8. 传感器的 Harmonic 适配

### 8.1 激光雷达

Classic 旧插件：

```xml
<sensor name="laserscan" type="ray">
  <plugin
    name="laserscan"
    filename="libgazebo_ros_ray_sensor.so"/>
</sensor>
```

Harmonic 使用原生 GPU Lidar：

```xml
<sensor name="laserscan" type="gpu_lidar">
  <always_on>true</always_on>
  <visualize>true</visualize>
  <update_rate>10</update_rate>
  <topic>/scan</topic>
  <ray>
    ...
  </ray>
</sensor>
```

ROS 桥接：

```text
/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan
```

在 Gazebo Harmonic 中查看扫描线：

```text
右上角菜单 → Plugins → Visualize Lidar → 选择 /scan
```

Harmonic 的显示效果可能是彩色射线或点，而不一定与 Classic 一样全部显示为
蓝色。

检查雷达：

```bash
gz topic -l | grep scan
ros2 topic echo /scan
```

### 8.2 IMU

Classic 旧插件：

```xml
<plugin
  name="imu_plugin"
  filename="libgazebo_ros_imu_sensor.so"/>
```

Harmonic 使用原生 IMU：

```xml
<sensor name="imu_sensor" type="imu">
  <always_on>true</always_on>
  <update_rate>100</update_rate>
  <topic>/imu</topic>
  <imu>
    ...
  </imu>
</sensor>
```

world 中还需要：

```xml
<plugin
  filename="gz-sim-imu-system"
  name="gz::sim::systems::Imu"/>
```

ROS 桥接：

```text
/imu@sensor_msgs/msg/Imu[gz.msgs.IMU
```

检查 IMU：

```bash
ros2 topic echo /imu
```

### 8.3 RGB-D 相机

Classic 旧插件：

```xml
<plugin
  name="depth_camera"
  filename="libgazebo_ros_camera.so"/>
```

Harmonic 使用：

```xml
<sensor name="camera_sensor" type="rgbd_camera">
  <always_on>true</always_on>
  <update_rate>10</update_rate>
  <topic>/camera</topic>
  <camera>
    ...
  </camera>
</sensor>
```

本项目还增加了标准 ROS 相机光学坐标系 `camera_optical_link`。

相机相关话题：

```text
/camera/image
/camera/depth_image
/camera/camera_info
/camera/points
```

查看图像：

```bash
ros2 run rqt_image_view rqt_image_view /camera/image
```

在 RViz 中可以添加：

- `Image`，选择 `/camera/image`；
- `PointCloud2`，选择 `/camera/points`。

如果仿真明显变卡，可以将相机分辨率从 `800×600` 降低为 `640×480` 或
`320×240`。

### 8.4 world 中的系统插件

Harmonic 中雷达和相机依赖 Sensors 系统，IMU 依赖 Imu 系统。

当前 world 显式启用了：

```xml
<plugin filename="gz-sim-physics-system"
        name="gz::sim::systems::Physics"/>

<plugin filename="gz-sim-user-commands-system"
        name="gz::sim::systems::UserCommands"/>

<plugin filename="gz-sim-scene-broadcaster-system"
        name="gz::sim::systems::SceneBroadcaster"/>

<plugin filename="gz-sim-imu-system"
        name="gz::sim::systems::Imu"/>

<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
```

当 world 开始显式声明系统插件时，应同时保留 Physics、UserCommands 和
SceneBroadcaster 等基础系统，否则可能出现物理不运行、无法生成模型或 GUI
无法更新场景等问题。

## 9. Xacro、URDF、TF 与 RViz 中遇到的问题

### 9.1 include 不等于创建模型

Xacro 文件中：

```xml
<xacro:include filename="..."/>
```

只是把宏定义引入当前文件，并不会自动创建 link。还需要调用宏：

```xml
<xacro:wheel_xacro .../>
<xacro:laser_xacro .../>
```

如果执行 Xacro 后只看到 `base`，首先检查其他部件的宏是否真的被调用。

### 9.2 Xacro 修改后仍然显示旧结果

`get_package_share_directory('fishbot_description')` 返回的是安装空间：

```text
chapt6_ws/install/fishbot_description/share/fishbot_description
```

不是源码目录。因此新增或修改文件后要重新构建并重新加载环境：

```bash
cd ~/chapt6/chapt6_ws
colcon build --packages-select fishbot_description --symlink-install
source install/setup.bash
```

使用 `--symlink-install` 可以减少 Python、launch、URDF 等资源文件修改后的
重复复制问题，但新增文件或安装规则变化时仍建议重新构建。

### 9.3 检查 Xacro 和 URDF

不要等到 Gazebo 启动失败后才检查模型，可以先执行：

```bash
xacro \
  ~/chapt6/chapt6_ws/src/fishbot_description/urdf/fishbot/fishbot.urdf.xacro \
  -o /tmp/fishbot.urdf
```

```bash
check_urdf /tmp/fishbot.urdf
```

检查转换后的 SDF：

```bash
gz sdf -p /tmp/fishbot.urdf > /tmp/fishbot.sdf
```

常见 Xacro/URDF 错误包括：

- 标签没有闭合；
- `xacro:` 拼写错误；
- 惯性宏名称不一致；
- 宏参数缺失；
- `origin`、`inertia` 或几何尺寸写错；
- include 路径指向不存在的文件；
- 新文件没有被安装到 share 目录。

### 9.4 模型有坐标和名字，但在 RViz 中看不见

如果 TF 中存在 caster 或其他 link，但模型不可见，应依次检查：

1. `<visual>` 是否存在；
2. 几何尺寸是否过小；
3. `origin` 是否把模型放进地面或车体内部；
4. 材质透明度 alpha 是否为 0；
5. Fixed Frame 是否正确；
6. RobotModel 是否成功读取 `/robot_description`。

TF 中有 link 只说明关节关系存在，并不能证明这个 link 一定具有可见几何体。

### 9.5 为什么轮子的父节点是 base_link

TF 父子关系来自 URDF 的 joint：

```xml
<joint name="left_wheel_joint" type="continuous">
  <parent link="base_link"/>
  <child link="left_wheel_link"/>
</joint>
```

不是由文件名、link 名字或 Gazebo 自动推断的。

### 9.6 为什么 TF 中没有 odom

`base_link`、轮子、雷达等关系来自 URDF，由 `robot_state_publisher` 发布。

`odom` 不是机器人身体上的固定 link，而是里程计坐标系。它通常由差速控制器
根据轮子运动动态发布：

```text
odom → base_footprint → base_link → sensors/wheels
```

本项目由 `fishbot_diff_drive_controller` 发布 `/odom`，并在
`enable_odom_tf: true` 时发布 `odom → base_footprint`。

检查：

```bash
ros2 topic echo /odom
ros2 run tf2_tools view_frames
```

### 9.7 XML 自动补全多出 `<`

如果在 VS Code 中已经输入 `<`，而补全插件插入的 snippet 本身也包含 `<`，
可能出现 `<<joint>`。

可尝试：

- 只输入 `joint` 后选择完整标签补全；
- 输入 `<joint` 时选择只补属性的建议；
- 暂时关闭冲突的 XML 自动补全扩展；
- 检查 URDF、XML、ROS 扩展是否同时提供了相同 snippet。

这属于编辑器补全冲突，不是 URDF 或 Xacro 语法要求。

## 10. World、模型资源与材质问题

### 10.1 为什么点击运行后物体会掉下去

Gazebo 点击运行后开始计算重力和碰撞。物体掉落通常是因为：

- 模型不是 `<static>true</static>`；
- 没有地面 collision；
- visual 存在但 collision 缺失；
- 模型初始高度不正确；
- 惯性或质量参数异常；
- collision 尺寸和 visual 不一致。

墙、地面和家具等固定环境模型通常应设置：

```xml
<static>true</static>
```

### 10.2 Harmonic 没有完整 Building Editor

Harmonic 没有 Classic 中同等完整的 Building Editor。建立墙壁可以：

- 在 SDF 中创建多个 static box；
- 创建独立的 `model.sdf`；
- 使用 Blender 等软件建模后导入；
- 导入 Classic world，再逐项修复资源和插件。

本项目中的房间模型由：

```text
world/room/model.config
world/room/model.sdf
```

描述，并由：

```text
world/custom_room.world
```

加载。

### 10.3 Classic world 能否直接使用

Classic `.world` 文件本质上也是 SDF，基础模型通常可以继续使用，但需要检查：

- Classic 专用插件；
- `model://` URI；
- 材质脚本；
- DAE 纹理路径；
- SDF 版本；
- world 系统插件；
- 保存文件中包含的大量 `<state>` 数据。

### 10.4 Gazebo 资源路径

Classic 常用：

```text
GAZEBO_MODEL_PATH
```

Harmonic 使用：

```text
GZ_SIM_RESOURCE_PATH
```

例如：

```bash
export GZ_SIM_RESOURCE_PATH="$HOME/.gazebo/models:/opt/ros/jazzy/share:$GZ_SIM_RESOURCE_PATH"
```

如果反复向 `~/.bashrc` 追加同一行，变量中会出现重复目录，例如：

```text
~/.gazebo/models:~/.gazebo/models:/opt/ros/jazzy/share
```

重复目录一般不会导致加载失败，但应清理 `~/.bashrc`，只保留一条配置。

Resource Spawner 中看不到某个模型，不代表 `/opt/ros/jazzy/share` 有问题，也
可能是模型目录没有加入 `GZ_SIM_RESOURCE_PATH`，或目录中缺少
`model.config` / `model.sdf`。

### 10.5 `model://cafe_table` 无法解析

典型错误：

```text
uri [model://cafe_table/meshes/cafe_table.dae] could not be resolved
Error Code 9: Failed to load a world
```

需要确认：

```text
~/.gazebo/models/cafe_table/model.config
~/.gazebo/models/cafe_table/model.sdf
~/.gazebo/models/cafe_table/meshes/cafe_table.dae
```

并确认：

```bash
echo "$GZ_SIM_RESOURCE_PATH"
```

包含：

```text
~/.gazebo/models
```

### 10.6 DAE 纹理路径错误

曾遇到：

```text
Could not resolve file [Wood_Floor_Dark.jpg]
Could not resolve file [Maple.jpg]
```

对应文件：

```text
~/.gazebo/models/cafe_table/meshes/cafe_table.dae
```

将：

```xml
<init_from>Wood_Floor_Dark.jpg</init_from>
<init_from>Maple.jpg</init_from>
```

改为：

```xml
<init_from>../materials/textures/Wood_Floor_Dark.jpg</init_from>
<init_from>../materials/textures/Maple.jpg</init_from>
```

### 10.7 Save World 与退出保存

建议使用明确的 `Save World As`，把 world 保存到项目的 `world/` 目录。
退出时的保存提示通常针对当前尚未保存的场景修改，容易覆盖原文件或保存到不
明确的位置。

GUI 布局、窗口位置和插件面板属于 GUI 配置，不等同于 world 中的模型、灯光
和物理配置。

## 11. 常见报错速查

### 11.1 `ros` 命令不存在

ROS 2 命令是：

```bash
ros2
```

不是：

```bash
ros
```

### 11.2 `file 'None' was not found`

错误命令：

```bash
ros2 launch ros_gz_sim
```

原因是没有指定 launch 文件。使用：

```bash
ros2 launch ros_gz_sim gz_sim.launch.py
```

### 11.3 `Package 'fishbot_description' not found`

```bash
cd ~/chapt6/chapt6_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select fishbot_description --symlink-install
source install/setup.bash
```

### 11.4 `/cmd_vel` 存在但小车不动

依次检查：

```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 topic info /cmd_vel -v
```

确认：

- `fishbot_diff_drive_controller` 为 `active`；
- 左右轮 velocity 接口为 `claimed`；
- `/cmd_vel` 类型为 `geometry_msgs/msg/TwistStamped`；
- `/cmd_vel` 至少有一个订阅者；
- Gazebo 仿真没有暂停；
- 没有同时加载第二个 DiffDrive 插件。

### 11.5 没有 `/cmd_vel`

话题通常只有在发布者或订阅者存在时才会显示。

本项目中 `fishbot_diff_drive_controller` 激活后会订阅 `/cmd_vel`。
如果控制器没有启动，检查 launch 中的 spawner 输出。

如果使用 Harmonic 原生 DiffDrive，则 `/cmd_vel` 是 Gazebo Transport 话题，
需要桥接；如果使用本项目的 `gz_ros2_control`，则不需要桥接控制话题。

### 11.6 TF 中没有轮子

检查：

```bash
ros2 topic echo /joint_states
ros2 control list_controllers
```

活动的 `joint_state_broadcaster` 应发布左右轮状态；
`robot_state_publisher` 根据这些状态计算并发布轮子 TF。

### 11.7 Gazebo GUI 中看不到雷达扫描

确认：

```xml
<visualize>true</visualize>
```

并在 GUI 中添加：

```text
Plugins → Visualize Lidar
```

选择 `/scan`。同时检查：

```bash
gz topic -l | grep scan
```

### 11.8 Gazebo 或 RViz 显示齿轮图标

Ubuntu Dock 显示齿轮通常表示应用没有匹配到正确的 `.desktop` 文件，和 ROS
或仿真功能无关。需要为启动命令创建 `.desktop` 文件，并正确配置：

```ini
Name=Gazebo Sim
Exec=gz sim
Icon=/absolute/path/to/icon.png
StartupWMClass=...
```

如果程序启动后仍显示齿轮，通常是 `StartupWMClass` 与实际窗口类不一致，可用：

```bash
xprop WM_CLASS
```

点击目标窗口后查询窗口类。

### 11.9 Git 提交提示“作者身份未知”

仅为当前仓库设置：

```bash
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

然后重新提交：

```bash
git commit -m "feat: FishROS URDF chapter for Gazebo Harmonic"
```

如果上传 GitHub，建议使用 GitHub 账户中已验证的邮箱。

## 12. 验证命令汇总

```bash
# 检查功能包
ros2 pkg prefix fishbot_description

# 检查 Xacro
xacro \
  ~/chapt6/chapt6_ws/src/fishbot_description/urdf/fishbot/fishbot.urdf.xacro \
  -o /tmp/fishbot.urdf

# 检查 URDF
check_urdf /tmp/fishbot.urdf

# 检查 SDF 转换
gz sdf -p /tmp/fishbot.urdf > /tmp/fishbot.sdf

# 检查控制器
ros2 control list_controllers
ros2 control list_hardware_interfaces

# 检查 ROS 话题
ros2 topic list

# 检查 Gazebo Transport 话题
gz topic -l

# 检查传感器
ros2 topic echo /scan
ros2 topic echo /imu

# 检查里程计
ros2 topic echo /odom
```

## 13. 参考资料

- [Gazebo Harmonic 文档](https://gazebosim.org/docs/harmonic/getstarted/)
- [Gazebo Classic 与 Gazebo Sim 功能对照](https://gazebosim.org/docs/harmonic/comparison/)
- [Gazebo Harmonic 传感器教程](https://gazebosim.org/docs/harmonic/sensors/)
- [ROS 2 与 Gazebo Harmonic 集成](https://gazebosim.org/docs/harmonic/ros2_integration/)
- [ros2_control Jazzy 文档](https://control.ros.org/jazzy/doc/getting_started/getting_started.html)
- [gz_ros2_control Jazzy 文档](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html)
- [diff_drive_controller Jazzy 文档](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)

## 14. 作者

- [CanggouBaiyun](https://github.com/CanggouBaiyun)

本项目用于个人 ROS 2 学习与 Gazebo Harmonic 迁移实践。

