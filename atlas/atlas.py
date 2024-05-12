import os

from log import logger


class Atlas:
    def __init__(self, connect=None):
        # 获取连接
        self.__client = connect.client()
        self.__world = connect.__world()
        # 获取地图
        self.__atlas = {os.path.basename(path): path for path in self.__client.get_available_maps()}

    # 获取可用地图
    def available_atlas(self):
        logger.info(f"The available atlas are:")
        logger.info(" ".join(self.__atlas.keys()))
        return self.__atlas

    # 获取当前地图名
    def current_map(self):
        # 获取当前地图名
        current_map = os.path.basename(self.__world.get_map().name)
        logger.info(f"The current map is {current_map}")
        return current_map

    # 切换地图
    def switch_map(self, map_name):
        # 判断输入是否正确
        if map_name in self.__atlas:
            # 切换地图
            self.__world = self.__client.load_world(self.__atlas[map_name])
            logger.info(f"world map success switch to {map_name}")

        else:
            logger.error(f"No such map")
