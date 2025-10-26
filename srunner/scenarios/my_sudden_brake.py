import carla
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenariomanager.scenarioatomics.atomic_triggers import InTriggerDistanceToVehicle
from srunner.scenarios.basic_scenario import BasicScenario
from srunner.tools.scenario_helper import get_waypoint_in_distance

# --- 这是针对你的版本，最终正确的代码 ---
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import (ActorTransformSetter,
                                                                        ActorDestroy,
                                                                        StopVehicle)
# --- 修改结束 ---
class MySuddenBrake(BasicScenario):
    """
    这是一个自定义的“前方车辆紧急刹车”场景。
    它继承了ScenarioRunner的BasicScenario类。
    """
    def __init__(self, world, ego_vehicles, config, randomize=False, debug_mode=False, criteria_enable=True,
                 timeout=60):
        self._other_actor_transform = None
        self._other_actor_target_velocity = 8 # 前车的行驶速度 (约30 km/h)
        self._ego_vehicle = ego_vehicles[0]
        super(MySuddenBrake, self).__init__("MySuddenBrake",
                                             ego_vehicles,
                                             config,
                                             world,
                                             debug_mode,
                                             criteria_enable=criteria_enable)

    def _initialize_actors(self, config):
        """创建场景中的演员（前车）"""
        waypoint, _ = get_waypoint_in_distance(self._ego_vehicle, 35)
        self._other_actor_transform = carla.Transform(
            carla.Location(waypoint.transform.location.x,
                           waypoint.transform.location.y,
                           waypoint.transform.location.z + 0.1),
            waypoint.transform.rotation)
        
        first_vehicle_bp = CarlaDataProvider.get_world().get_blueprint_library().find('vehicle.toyota.prius')
        first_vehicle = CarlaDataProvider.request_new_actor(first_vehicle_bp, self._other_actor_transform)
        self.other_actors.append(first_vehicle)

    def _create_behavior(self):
        """定义场景的行为（剧本）"""
        # 1. 让前车先自动驾驶
        behaviour = self.get_actor_behavior(self.other_actors[0], start_vel=self._other_actor_target_velocity)

        # 2. 定义触发条件：当我们的车距离前车小于20米时
        trigger_distance = InTriggerDistanceToVehicle(self.other_actors[0], self._ego_vehicle, 20)
        
        # 3. 定义触发后发生的动作：前车紧急刹车 (刹车力度1.0)
        brake_action = StopVehicle(self.other_actors[0], 1.0)

        # 4. 将触发条件和动作组合起来
        behaviour.trigger_sequence(trigger_distance, brake_action)
        return behaviour

    def _create_test_criteria(self):
        """定义场景的成功/失败条件"""
        return [CollisionTest(self._ego_vehicle)]

    def __del__(self):
        """场景结束时，清理所有演员"""
        self.remove_all_actors()