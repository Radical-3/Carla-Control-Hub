import random

import carla
from carla import Location, Rotation

from actor import Vehicle
from log import logger
from .base_factory import Base_Factory


class Vehicle_Factory(Base_Factory):
    def __init__(self, connect):
        super().__init__(connect)
        self.__blueprint_library = self._blueprint_library.filter('vehicle.*.*')
        self.__spawn_points = list(self._world.get_map().get_spawn_points())

    def spawn_actor(self, name=None, spawn_point=None):
        vehicle = None
        if len(self.__spawn_points) > 0:
            # 若姓名不为空且在蓝图库中,生成指定蓝图车辆，否则随机选择蓝图生成车辆
            if name is not None and self.__blueprint_library.find("vehicle." + name):
                logger.debug(f"Spawn vehicle named {name}")
                blueprint = self.__blueprint_library.find("vehicle." + name)
            else:
                logger.debug(f"Spawn vehicle randomly")
                blueprint = random.choice(list(self.__blueprint_library))
            if spawn_point is None:
                logger.debug(f"Spawn at random point")
                spawn_point = random.choice(self.__spawn_points)
            else:
                logger.debug(f"Spawn at the specified point")
                if len(spawn_point) == 3:
                    spawn_point = spawn_point.extend([0, 0, 0])
                spawn_point = carla.Transform(Location(x=spawn_point[0], y=spawn_point[1], z=spawn_point[2]),
                                              Rotation(pitch=spawn_point[3], yaw=spawn_point[4], roll=spawn_point[5]))
            vehicle = Vehicle(self._world, blueprint, spawn_point)
        else:
            logger.error(f"No spawn points remaining")

        if vehicle.exist():
            logger.debug(f"Spawn a vehicle successfully,id is {vehicle.id()}")
            self._actor_id_list.append(vehicle.id())
            self.__spawn_points.remove(spawn_point)
            return vehicle
        else:
            logger.error(f"Spawn vehicle failed")

    def spawn_batch_actor(self, batch, name=None):
        # 判断是否仍有剩余生成点
        if len(self.__spawn_points) > 0:
            # 若没有充足剩余生成点
            if batch > len(self.__spawn_points):
                logger.warning(
                    f"There are not enough spawn points left,Only {len(self.__spawn_points)} Vehicles can be produced")
                batch = len(self.__spawn_points)
            vehicle_list = list()
            # 循环生成车辆
            for i in range(batch):
                # 根据是否指定蓝图名，选择指定或随机蓝图
                if name is not None and self._blueprint_library.find("vehicle." + name):
                    blueprint = self._blueprint_library.find("vehicle." + name)
                else:
                    blueprint = random.choice(list(self._blueprint_library))
                spawn_point = random.choice(self.__spawn_points)
                vehicle = Vehicle(self._world, blueprint, spawn_point)
                # 判断是否生成成功，生成成功则加入全体列表已经当前列表，失败则归还生成点，并报错
                if vehicle.exist():
                    self._actor_id_list.append(vehicle.id())
                    vehicle_list.append(vehicle)
                    self.__spawn_points.remove(spawn_point)
                else:
                    logger.error(f"Spawn vehicle failed")
            logger.debug(f"Spawn {len(vehicle_list)} vehicles successfully")
            return vehicle_list

        else:
            logger.error(f"No spawn points remaining")

    def production(self, vehicle_id):
        vehicle = Vehicle(self._world, actor_id=vehicle_id)
        return vehicle

    def enable_all_vehicle_autopilot(self, state=True, traffic_manager_port=800):
        for vehicle_id in self._actor_id_list:
            vehicle = Vehicle(self._world, actor_id=vehicle_id)
            vehicle.set_autopilot(state, traffic_manager_port)

    def destroy_actor(self, vehicle):
        if vehicle.id() in self._actor_id_list:
            state = vehicle.destroy()
            self._actor_id_list.remove(vehicle.id())
            if state:
                logger.debug(f"Destroy vehicle successfully")
            else:
                logger.error(f"Destroy vehicle failed")
        else:
            logger.error(f"do not use this factory")

    def clear_factory(self):
        for vehicle_id in self._actor_id_list:
            vehicle = Vehicle(self._world, actor_id=vehicle_id)
            state = vehicle.destroy()
            if not state:
                logger.error(f"Destroy vehicle failed")
        self._actor_id_list.clear()
        logger.debug(f"Clear vehicle factory successfully")
