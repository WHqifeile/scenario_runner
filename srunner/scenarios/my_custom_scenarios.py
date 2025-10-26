#!/usr/bin/env python

# 导入所有必要的模块
import py_trees
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter, 
                                                                       LaneChange, 
                                                                       ActorDestroy, 
                                                                       WaitForever)
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_trigger_conditions import InTriggerDistanceToVehicle
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_waypoint_in_distance

# 1. 定义我们自己的场景类，它必须继承自 BasicScenario
class SuddenCutInScenario(BasicScenario):
    """
    这是一个自定义的接管场景。
    一辆背景车辆会在主车靠近时，突然切入到主车前方。
    """
    
    # 2. __init__: 准备阶段，从XML配置文件中读取参数
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True, timeout=60):
        """
        初始化所有场景参数
        """
        # 从config中获取自定义参数，如果XML没提供，就使用默认值
        # 'other_parameters' 对应XML中的 <other_parameters>
        self._other_actor_target_speed = config.other_parameters.get('target_speed', 10) # 切入车辆的目标速度
        self._trigger_distance = config.other_parameters.get('trigger_distance', 30)   # 触发危险事件的距离
        self._cut_in_distance = config.other_parameters.get('cut_in_distance', 10)     # 切入后与主车的距离

        # 调用父类的构造函数，这是必须的
        super(SuddenCutInScenario, self).__init__("SuddenCutInScenario",
                                                  ego_vehicles,
                                                  config,
                                                  world,
                                                  debug_mode,
                                                  criteria_enable=criteria_enable)

    # 3. _initialize_actors: 创建危险车辆
    def _initialize_actors(self, config):
        """
        在场景开始时，创建我们需要的危险车辆，并把它放在起始位置zx
        """
        # 在主车侧方车道前方某处，找到一个生成点
        waypoint, _ = get_waypoint_in_distance(self.ego_vehicles[0].get_world().get_map().get_waypoint(self.ego_vehicles[0].get_location()), 50)
        # 确保它在左侧或右侧车道 (这里以右侧为例)
        self.other_actor_waypoint = waypoint.get_right_lane()

        # 创建危险车辆 actor_transform_setter
        # 'rolename'='other_actor' 是我们给它起的代号
        self.other_actor_transform = self.other_actor_waypoint.transform
        self.other_actor = CarlaDataProvider.request_new_actor('vehicle.tesla.model3', 
                                                               self.other_actor_transform,
                                                               rolename='other_actor')
        self.other_actor.set_simulate_physics(enabled=True) # 开启物理模拟

        # 将创建的演员添加到场景的演员列表中，以便场景结束时自动清理
        self.other_actors.append(self.other_actor)

    # 4. _create_behavior: 定义核心行为逻辑 (最关键的部分)
    def _create_behavior(self):
        """
        定义危险车辆的行为：等待触发 -> 突然切入
        """
       
        sequence = py_trees.composites.Sequence("CutInAction")

        # 任务1: 等待触发条件
        # 当主车(ego_vehicles[0])与我们创建的危险车(other_actor)距离小于_trigger_distance时，此任务完成
        sequence.add_child(InTriggerDistanceToVehicle(self.other_actor, self.ego_vehicles[0], self._trigger_distance))

        # 任务2: 执行切入动作
        # 使用 LaneChange 原子行为，让危险车辆向左变道 ('LEFT')
        # target_lane_distance: 变道后与主车的距离
        # speed: 变道时的速度
        sequence.add_child(LaneChange(self.other_actor, 
                                      speed=self._other_actor_target_speed, 
                                      direction='left', 
                                      distance_same_lane=self._cut_in_distance))
        
        # 任务3: 保持场景运行
        # 切入动作完成后，让场景继续运行下去，以便CollisionTest可以持续检测碰撞
        sequence.add_child(WaitForever())

        return sequence

    # 5. _create_test_criteria: 定义成功/失败的规则
    def _create_test_criteria(self):
        """
        定义核心的测试标准：碰撞检测
        """
        # 创建一个碰撞检测器，它会持续监控主车是否发生碰撞
        collision_criterion = CollisionTest(self.ego_vehicles[0])
        return [collision_criterion]

    # 6. __del__: 场景结束后的清理工作
    def __del__(self):
        """
        场景结束时，移除所有创建的演员
        """
        self.remove_all_actors()