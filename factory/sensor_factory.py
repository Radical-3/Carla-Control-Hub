from actor import Camera
from log import logger
from .base_factory import Base_Factory


class Sensor_Factory(Base_Factory):
    def __init__(self, connect):
        # 获取连接
        super().__init__(connect)
        self.__blueprint_library = self._blueprint_library.filter('sensor.*.*')
        self.__arguments = dict()

        # 创造相机

    def spawn_actor(self, category=None, attach=None, image_size=None, fov=None, offset=None):
        if not all([category, attach, image_size, fov, offset]):
            logger.error("miss parameter")
            return
        blueprint = self._world.get_blueprint_library().find('sensor.' + category)
        sensor = Camera(self._world, blueprint, attach, image_size, fov, offset)
        self._actor_id_list.append(sensor.id())
        self.__arguments[sensor.id()] = [blueprint, attach, image_size, fov, offset]
        logger.debug(f"Spawn a {category} successfully,id is {sensor.id()}")
        return sensor

    def production(self, sensor_id):
        sensor = None
        if sensor_id in self._actor_id_list:
            arguments = self.__arguments[sensor_id]
            sensor = Camera(self._world, arguments[0], arguments[1], arguments[2], arguments[3], arguments[4],
                            sensor_id)
        else:
            logger.warning(f"the actor not spawn by this factory")
        return sensor

    # 销毁传感器
    def destroy_actor(self, sensor):
        if sensor.id() in self._actor_id_list:
            state = sensor.destroy()
            if state:
                self._actor_id_list.remove(sensor.id())
                self.__arguments.pop(sensor.id())
                logger.debug(f"Destroy sensor successfully")
            else:
                logger.error(f"Destroy sensor failed")
        else:
            logger.error(f"do not use this factory")

    def clear_factory(self):
        for sensor_id in self._actor_id_list:
            arguments = self.__arguments[sensor_id]
            sensor = Camera(self._world, arguments[0], arguments[1], arguments[2], arguments[3], arguments[4],
                            sensor_id)
            state = sensor.destroy()
            if not state:
                logger.error(f"Destroy sensor failed")
        self._actor_id_list.clear()
        self.__arguments.clear()
        logger.debug(f"Clear sensor factory successfully")
