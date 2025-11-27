import math
import os
import queue
import time
from queue import Queue
from random import random

import carla
import cv2

from config import Config
from connect import Connect
from factory import Vehicle_Factory, Sensor_Factory
from log import logger
from processor import Processor

from utils import generate_random_offset, package, generate_specify_offset, set_traffic_light_to_wait_seconds, move_camera_with_noise
from weather import Weather


def dataset_generate4():

    config = Config(logger, './config/base.yaml').item()
    logger.set_config(config)

    connect = Connect(config)
    # 列出所有可用地图
    available_maps = connect.client().get_available_maps()
    print("Available maps:", available_maps)

    # 加载指定地图
    connect.load_world('Town07')
    # 修改红灯的等待时间
    set_traffic_light_to_wait_seconds(connect.world(), 0, 0)
    processor = Processor(config, connect)
    weather = Weather(connect)
    weather.switch_by_presets("CloudySunset")
    vehicle_factory = Vehicle_Factory(connect)
    sensor_factory = Sensor_Factory(connect)

    # vehicle = vehicle_factory.spawn_actor("audi.etron")
    spawn_point = [-9125.87,5703.02,103.48,0,0,3.26]
    # vehicle = vehicle_factory.spawn_actor("audi.etron")
    vehicle, vehicle_transform = vehicle_factory.spawn_spec_actor("audi.etron", 5)
    vehicle_factory.enable_all_vehicle_autopilot(True, config.traffic_manager_port)

    path = os.path.join(str(config.dataset_path), str(config.dataset_name))
    image_path = os.path.join(path, "image")
    semantic_segmentation_path = os.path.join(path, "semantic_segmentation")
    camera_position_path = os.path.join(path, "camera_position")
    label_path = os.path.join(path, "label")

    os.makedirs(image_path)
    os.makedirs(semantic_segmentation_path)
    os.makedirs(camera_position_path)
    os.makedirs(label_path)

    start_time = int(1715443200)
    offset = generate_specify_offset(config)
    # camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
    camera_queue = queue.Queue()
    semantic_queue = queue.Queue()
    camera = sensor_factory.spawn_spec_actor("camera.rgb", vehicle_transform, config.image_size, config.fov, offset)

    # 这里暂停一会是因为刚开始车会从天上掉下来，这时候不用拍照
    time.sleep(2)
    # listen是每次获取到图片就把图片传到()中的函数里并调用
    camera.actor.listen(lambda image: processor.listen_rgb(image, camera_queue))


    # 这是加上了随机小幅度偏移相机，但是实际来看好像偏移的太大了
    # camera.actor.listen(lambda image: (camera_queue.put(image), move_camera_with_noise(camera)))
    camera_semantic_segmentation = processor.add_camera_return_seman_camera(camera)
    camera_semantic_segmentation.actor.listen(semantic_queue.put)
    # camera_semantic_segmentation.actor.listen(lambda image: (semantic_queue.put(image), move_camera_with_noise(camera_semantic_segmentation)))
    camera.clear_picture_queue()
    camera_semantic_segmentation.clear_picture_queue()
    flag = 0
    for i in range(config.dataset_generate_image_num):
        # offset = generate_random_offset(config)
        # camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
        # processor.add_camera(camera)
        if camera_queue.qsize() > config.dataset_generate_image_num or semantic_queue.qsize() > config.dataset_generate_image_num:
            if flag == 0:
                camera.actor.stop()
                camera_semantic_segmentation.actor.stop()
                flag = 1
        # 这是干啥的来着？？
        time.sleep(config.dataset_generate_interval)
        image, semantic_segmentation, labels, position = processor.process_queue(camera_queue, semantic_queue)
        identifier = round(time.time() - start_time + 1)

        cv2.imwrite(os.path.join(image_path, f"{identifier}.png"), image)
        cv2.imwrite(os.path.join(semantic_segmentation_path, f"{identifier}.png"), semantic_segmentation)
        with open(os.path.join(camera_position_path, f"{identifier}.txt"), 'a+') as f:
            f.write(f"{position[0]} {position[1]} {position[2]}")
        with open(os.path.join(label_path, f"{identifier}.txt"), 'a+') as f:
            for label in labels:
                f.write(f"{label[0]} {label[1]} {label[2]} {label[3]}\n")
        # processor.remove_camera()
        # sensor_factory.destroy_actor(camera)

    processor.remove_camera()
    sensor_factory.destroy_actor(camera)
    vehicle_factory.enable_all_vehicle_autopilot(False, config.traffic_manager_port)
    vehicle_factory.destroy_actor(vehicle)
    vehicle_factory.clear_factory()
    sensor_factory.clear_factory()
    processor.destroy()

    package(config)
