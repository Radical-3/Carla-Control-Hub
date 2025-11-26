import os
import time
import carla
import cv2
from PIL import Image
from config import Config
from connect import Connect
from factory import Vehicle_Factory, Sensor_Factory
from log import logger
from processor import Processor

from utils import generate_random_offset, package
from weather import Weather


def update():
    config = Config(logger, './config/base.yaml').item()
    logger.set_config(config)

    connect = Connect(config)
    processor = Processor(config, connect)
    weather = Weather(connect)
    weather.switch_by_presets("CloudySunset")
    vehicle_factory = Vehicle_Factory(connect)
    sensor_factory = Sensor_Factory(connect)

    vehicle = vehicle_factory.spawn_actor("audi.asymmetric")
    vehicle_factory.enable_all_vehicle_autopilot(True, config.traffic_manager_port)
    time.sleep(20)
    image_path = "resized_image2.jpg"
    image = Image.open(image_path)
    height = image.size[1]
    width = image.size[0]
    texture = carla.TextureColor(width, height)
    for x in range(width):
        for y in range(height):
            color = image.getpixel((x, y))
            r, g, b = color[0], color[1], color[2]
            a = 255  # Alpha通道，设为不透明
            texture.set(x, y, carla.Color(r, g, b, a))
    world = connect.world()

    # MI_CarExterior_Etron_BaseColor_Mat
    world.apply_color_texture_to_object("audi_asymmetric_C_0", carla.MaterialParameter.Diffuse, texture)
    print(list(world.get_names_of_all_objects()))
    time.sleep(120)
    vehicle_factory.enable_all_vehicle_autopilot(False, config.traffic_manager_port)
    vehicle_factory.destroy_actor(vehicle)
    vehicle_factory.clear_factory()
