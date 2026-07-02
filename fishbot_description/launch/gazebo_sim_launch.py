import os

from ament_index_python.packages import get_package_share_directory
import launch
import launch_ros
import launch_ros.parameter_descriptions


def generate_launch_description():
    # 获取功能包的 share 目录。
    urdf_package_path = get_package_share_directory('fishbot_description')
    default_xacro_path = os.path.join(
        urdf_package_path, 'urdf', 'fishbot', 'fishbot.urdf.xacro'
    )
    default_gazebo_world_path = os.path.join(
        urdf_package_path, 'world', 'custom_room.world'
    )
    gz_launch_path = os.path.join(
        get_package_share_directory('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py'
    )

    # 声明模型路径参数，方便在命令行中替换。
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model',
        default_value=str(default_xacro_path),
        description='加载的模型文件路径'
    )

    substitutions_command_result = launch.substitutions.Command([
        'xacro ',
        launch.substitutions.LaunchConfiguration('model')
    ])
    robot_description_value = (
        launch_ros.parameter_descriptions.ParameterValue(
            substitutions_command_result,
            value_type=str
        )
    )

    action_robot_state_publisher = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description_value}]
    )

    action_launch_gazebo = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            gz_launch_path
        ),
        launch_arguments={
            'gz_args': f'-r -v 4 {default_gazebo_world_path}',
            'on_exit_shutdown': 'true'
        }.items()
    )

    action_spawn_entity = launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'default',
            '-topic', '/robot_description',
            '-name', 'fishbot',
            '-z', '0.2'
        ],
        output='screen'
    )

    # gz_ros2_control 会直接创建 ROS 2 controller_manager，所以控制话题无需桥接。
    action_sensor_bridge = launch_ros.actions.Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked'
        ],
        output='screen'
    )

    action_joint_state_broadcaster = launch_ros.actions.Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60'
        ],
        output='screen'
    )

    action_diff_drive_controller = launch_ros.actions.Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'fishbot_diff_drive_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60'
        ],
        output='screen'
    )

    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        action_robot_state_publisher,
        action_launch_gazebo,
        action_spawn_entity,
        action_sensor_bridge,
        action_joint_state_broadcaster,
        action_diff_drive_controller
    ])
