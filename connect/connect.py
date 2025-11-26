import carla

from log import logger


class Connect:
    def __init__(self, config):
        self.__config = config
        self.__client = carla.Client(self.__config.host, self.__config.service_port)

        self.__client.set_timeout(self.__config.timeout)
        logger.info('client success create')

        self.__world = self.__client.get_world()
        logger.info('world success connect')

        if config.world_reload:
            self.__client.reload_world(reset_settings=True)
            logger.info('world success reload')

        self.__trafficmanager = None
        self.__init_settings = None
        self.__settings = None

    def client(self):
        return self.__client

    def world(self):
        return self.__world

    def tick(self):
        if self.__settings:
            self.__world.tick()
        else:
            logger.error("set async True first")

    def load_world(self, town):
        self.__world = self.__client.load_world(town)

    def get_traffic_manager_port(self):
        if self.__trafficmanager is None:
            self.__trafficmanager = self.__client.get_trafficmanager(self.__config.traffic_manager_port)
            self.__trafficmanager.global_percentage_speed_difference(self.__config.vehicle_speed_limit)
        return self.__config.traffic_manager_port

    def async_traffic_manager(self, status):
        if status:
            self.__init_settings = self.__world.get_settings()
            self.__settings = self.__world.get_settings()
            self.__settings.fixed_delta_seconds = self.__config.fixed_delta_seconds
            self.__settings.synchronous_mode = True
            self.__world.apply_settings(self.__settings)
            self.__trafficmanager.set_synchronous_mode(True)
        else:
            self.__init_settings.synchronous_mode = False
            self.__world.apply_settings(self.__init_settings)
            self.__trafficmanager.set_synchronous_mode(False)
            self.__settings = None
