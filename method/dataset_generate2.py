import os
import queue
import time
from queue import Queue

import cv2

from config import Config
from connect import Connect
from factory import Vehicle_Factory, Sensor_Factory
from log import logger
from processor import Processor

from utils import generate_random_offset, package, generate_specify_offset, set_traffic_light_to_wait_seconds
from weather import Weather


# 模拟相机抖动
def dataset_generate():
    config = Config(logger, './config/base.yaml').item()
    logger.set_config(config)

    connect = Connect(config)
    # 修改红灯的等待时间
    set_traffic_light_to_wait_seconds(connect.world(), 0.2, 0.2)
    processor = Processor(config, connect)
    weather = Weather(connect)
    weather.switch_by_presets("CloudySunset")
    vehicle_factory = Vehicle_Factory(connect)
    sensor_factory = Sensor_Factory(connect)

    vehicle = vehicle_factory.spawn_actor("audi.asymmetric")
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
    camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
    processor.add_camera(camera)
    # 这里暂停一会是因为刚开始车会从天上掉下来，这时候不用拍照
    time.sleep(20)
    # listen是每次获取到图片就把图片传到()中的函数里并调用
    camera.actor.listen(camera_queue.put)
    camera_semantic_segmentation = processor.add_camera(camera)
    camera_semantic_segmentation.actor.listen(semantic_queue.put)
    camera.clear_picture_queue()
    camera_semantic_segmentation.clear_picture_queue()
    flag = 0
    for i in range(config.dataset_generate_image_num):
        # offset = generate_random_offset(config)
        # camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
        # processor.add_camera(camera)
        if camera_queue.qsize() > 100 or semantic_queue.qsize() > 100:
            if flag == 0:
                camera.actor.stop()
                camera_semantic_segmentation.actor.stop()
                flag = 1
        # 这是干啥的来着？？
        time.sleep(config.dataset_generate_interval)
        image, semantic_segmentation, labels, position = processor.process(camera_queue, semantic_queue)
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
