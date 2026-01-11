import os
import sys
import yaml
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command
sys.path.append(os.path.join(get_package_share_directory('rm_bringup'), 'launch'))


def generate_launch_description():

    from launch_ros.descriptions import ComposableNode
    from launch_ros.actions import ComposableNodeContainer, Node, SetParameter, PushRosNamespace
    from launch.actions import TimerAction, Shutdown
    from launch import LaunchDescription

    launch_params = yaml.safe_load(open(os.path.join(
        get_package_share_directory('rm_bringup'), 'config', 'launch_params.yaml')))

    SetParameter(name='rune',value=launch_params['rune']),
    robot_gimbal_description = Command(['xacro ', os.path.join(
        get_package_share_directory('rm_robot_description'), 'urdf', 'rm_gimbal.urdf.xacro'),
        ' xyz:=', launch_params['odom2camera']['xyz'], ' rpy:=', launch_params['odom2camera']['rpy']])
    
    robot_navigation_description = Command(['xacro ', os.path.join(
        get_package_share_directory('rm_robot_description'), 'urdf', 'sentry.urdf.xacro')])

    robot_gimbal_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_gimbal_description,
                    'publish_frequency': 1000.0}]
    )
    
    robot_navigation_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_navigation_description,}]
    )

    def get_params(name):
        return os.path.join(get_package_share_directory('rm_bringup'), 'config', 'node_params', '{}_params.yaml'.format(name))

    # 串口
    if launch_params['virtual_serial']:
        serial_driver_node = Node(
            package='rm_serial_driver',
            executable='virtual_serial_node',
            name='virtual_serial',
            output='both',
            emulate_tty=True,
            parameters=[get_params('virtual_serial')],
            ros_arguments=['--ros-args', '-p', 'has_rune:=true' if launch_params['rune'] else 'has_rune:=false'],
        )
    else:
        serial_driver_node = Node(
            package='rm_serial_driver',
            executable='rm_serial_driver_node',
            name='serial_driver',
            output='both',
            emulate_tty=True,
            parameters=[get_params('serial_driver')],
            ros_arguments=['--ros-args', ],
        )

    light_type = launch_params.get('light_type', 'red')  # 默认为红色 
    
    # 装甲板识别
    if light_type == 'red':    
        armor_detector_node = ComposableNode(
            package='armor_detector', 
            plugin='fyt::auto_aim::ArmorDetectorNode',
            name='armor_detector',
            parameters=[get_params('armor_detector_R')],
            extra_arguments=[{'use_intra_process_comms': True}]
        )
    elif light_type == 'blue':    
        armor_detector_node = ComposableNode(
            package='armor_detector', 
            plugin='fyt::auto_aim::ArmorDetectorNode',
            name='armor_detector',
            parameters=[get_params('armor_detector_B')],
            extra_arguments=[{'use_intra_process_comms': True}]
        )
    else:
        armor_detector_node = ComposableNode(
            package='armor_detector', 
            plugin='fyt::auto_aim::ArmorDetectorNode',
            name='armor_detector',
            parameters=[get_params('armor_detector_R')],  # 默认使用红色参数
            extra_arguments=[{'use_intra_process_comms': True}]
        )
    
    # 装甲板解算
    if launch_params['hero_solver']:
        armor_solver_node = Node(
            package='hero_armor_solver',
            executable='hero_armor_solver_node',
            name='armor_solver',
            output='both',
            emulate_tty=True,
            parameters=[get_params('armor_solver')],
            ros_arguments=[],
        )
    else:
        if light_type == 'red': 
            armor_solver_node = Node(
                package='armor_solver',
                executable='armor_solver_node',
                name='armor_solver',
                output='both',
                emulate_tty=True,
                parameters=[get_params('armor_solver_R')],
                ros_arguments=[],
            )
        elif light_type == 'blue':
            armor_solver_node = Node(
                package='armor_solver',
                executable='armor_solver_node',
                name='armor_solver',
                output='both',
                emulate_tty=True,
                parameters=[get_params('armor_solver_B')],
                ros_arguments=[],
            )
        else:
            armor_solver_node = Node(
                package='armor_solver',
                executable='armor_solver_node',
                name='armor_solver',
                output='both',
                emulate_tty=True,
                parameters=[get_params('armor_solver_R')],  # 默认使用红色参数
                ros_arguments=[],
            )

    # 打符
    if launch_params['rune']:
        if light_type == 'red':
            rune_detector_node = ComposableNode(    
                package='rune_detector',
                plugin='fyt::rune::RuneDetectorNode',
                name='rune_detector',
                parameters=[get_params('rune_detector_R')],
                extra_arguments=[{'use_intra_process_comms': True}]
                )
            rune_solver_node = Node(
                package='rune_solver',
                executable='rune_solver_node',
                name='rune_solver',
                output='both',
                emulate_tty=True,
                parameters=[get_params('rune_solver_R')],
                arguments=['--ros-args',], 
                )
        elif light_type == 'blue':
            rune_detector_node = ComposableNode(    
                package='rune_detector',
                plugin='fyt::rune::RuneDetectorNode',
                name='rune_detector',
                parameters=[get_params('rune_detector_B')],
                extra_arguments=[{'use_intra_process_comms': True}]
                )
            rune_solver_node = Node(
                package='rune_solver',
                executable='rune_solver_node',
                name='rune_solver',
                output='both',
                emulate_tty=True,
                parameters=[get_params('rune_solver_B')],
                arguments=['--ros-args',], 
                )
        else:
            rune_detector_node = ComposableNode(    
                package='rune_detector',
                plugin='fyt::rune::RuneDetectorNode',
                name='rune_detector',
                parameters=[get_params('rune_detector_R')],  # 默认使用红色参数
                extra_arguments=[{'use_intra_process_comms': True}]
                )
            rune_solver_node = Node(
                package='rune_solver',
                executable='rune_solver_node',
                name='rune_solver',
                output='both',
                emulate_tty=True,
                parameters=[get_params('rune_solver_R')],  # 默认使用红色参数
                arguments=['--ros-args',], 
                )

    # 修改容器创建函数 - 不再包含相机节点
    def get_detector_container(*detector_nodes):
        nodes_list = list(detector_nodes)
        container = ComposableNodeContainer(
            name='detector_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container_mt',
            composable_node_descriptions=nodes_list,
            output='both',
            emulate_tty=True,
            ros_arguments=['--ros-args', ],
        )
        return TimerAction(
            period=2.0,
            actions=[container],
        )

    # 延迟启动
    delay_serial_node = TimerAction(
        period=1.5,
        actions=[serial_driver_node],
    )

    delay_armor_solver_node = TimerAction(
        period=2.0,
        actions=[armor_solver_node],
    )
    
    # 创建检测器容器
    if launch_params['rune']:
        detector_node = get_detector_container(armor_detector_node, rune_detector_node)
        delay_rune_solver_node = TimerAction(
            period=2.0,
            actions=[rune_solver_node],
        )
    else:
        detector_node = get_detector_container(armor_detector_node)
        delay_rune_solver_node = None

    delay_detector_node = TimerAction(
        period=2.0,
        actions=[detector_node],
    ) 
    
    push_namespace = PushRosNamespace(launch_params['namespace'])
    
    # 构建启动列表
    launch_description_list = [
        robot_gimbal_publisher,
        push_namespace,
        delay_serial_node,
        delay_detector_node,
        delay_armor_solver_node]
    
    if launch_params['rune'] and delay_rune_solver_node:
        launch_description_list.append(delay_rune_solver_node)
    
    if launch_params['navigation']:
        launch_description_list.append(robot_navigation_publisher)
    
    return LaunchDescription(launch_description_list)