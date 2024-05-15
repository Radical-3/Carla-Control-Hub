import inspect

import carla

from log import logger


class Weather:
    def __init__(self, connect):
        self.__client = connect.client()
        self.__world = connect.world()
        # 用于保存预设天气的字典
        self.__presets = dict()
        # 用于保存天气参数的字典
        self.__parameters = dict()
        # 获取天气属性下的名称及值(包括预设天气参数和各个天气参数),并存入字典
        for name, value in inspect.getmembers(self.__world.get_weather()):
            # 预设天气参数以大写开头，天气参数以小写开头
            if name[0].isupper():
                self.__presets[name] = value
            elif name[0].islower():
                self.__parameters[name] = value

    def presets(self):
        # 打印所有的预设天气
        logger.debug("The weather presets are as follows:")
        logger.debug(" | ".join(sorted(list(self.__presets.keys()))))
        return self.__presets.keys()

    def parameters(self):
        # 打印所有的天气参数
        logger.debug("The weather parameters are as follows:")
        logger.debug(" | ".join(sorted(list(self.__parameters.keys()))))
        return self.__parameters.keys()

    def get_current_parameters(self):
        # 打印当前天气参数及其值
        logger.debug("The current weather parameters  are as follows:")
        logger.debug(" | ".join(
            [f"- {parameter} : {self.__parameters[parameter]}" for parameter in
             sorted(list(self.__parameters.keys()))]))
        return self.__parameters

    def switch_by_presets(self, weather):
        # 判断是否存在该预设天气
        if weather in self.__presets.keys():
            # 切换天气
            self.__world.set_weather(self.__presets[weather])
            logger.debug(f"world weather success switch to {weather}")
        else:
            logger.error("No such preset weather")

    def switch_by_parameters(self, parameters):
        # 判断是否存在该天气参数
        for parameter in parameters:
            if parameter in self.__parameters.keys():
                # 将输入的天气参数赋值给当前天气参数
                self.__parameters[parameter] = parameters[parameter]
            else:
                logger.debug(f"No such weather parameter named {parameter}")
        # 根据当前天气修改天气
        self.__world.set_weather(carla.WeatherParameters(**self.__parameters))
