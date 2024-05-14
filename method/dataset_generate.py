import os
import time

import cv2

from config import Config
from connect import Connect
from factory import Vehicle_Factory, Sensor_Factory
from log import logger
from processor import Processor

from utils import generate_random_offset, package


def dataset_generate():
    config = Config(logger, './config/base.yaml').item()
    logger.set_config(config)

    connect = Connect(config)
    processor = Processor(config, connect)
    vehicle_factory = Vehicle_Factory(connect)
    sensor_factory = Sensor_Factory(connect)

    vehicle = vehicle_factory.spawn_actor("audi.etron")
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
    for i in range(config.dataset_generate_image_num):
        offset = generate_random_offset(config)
        camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
        time.sleep(config.dataset_generate_interval)

        processor.add_camera(camera)
        image, semantic_segmentation, labels, position = processor.process()
        identifier = round(time.time() - start_time + 1)

        cv2.imwrite(os.path.join(image_path, f"{identifier}.png"), image)
        cv2.imwrite(os.path.join(semantic_segmentation_path, f"{identifier}.png"), semantic_segmentation)
        with open(os.path.join(camera_position_path, f"{identifier}.txt"), 'a+') as f:
            f.write(f"{position[0]} {position[1]} {position[2]}")
        with open(os.path.join(label_path, f"{identifier}.txt"), 'a+') as f:
            for label in labels:
                f.write(f"{label[0]} {label[1]} {label[2]} {label[3]}\n")
        processor.remove_camera()
        sensor_factory.destroy_actor(camera)

    vehicle_factory.enable_all_vehicle_autopilot(False, config.traffic_manager_port)
    vehicle_factory.destroy_actor(vehicle)
    vehicle_factory.clear_factory()
    sensor_factory.clear_factory()
    processor.destroy()

    package(config)
