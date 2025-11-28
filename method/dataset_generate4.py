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
    # camera_queue = queue.Queue()
    # semantic_queue = queue.Queue()
    # 同步队列，用于存储配对的RGB和语义分割图像
    sync_queue = queue.Queue()
    
    # 这里暂停一会是因为刚开始车会从天上掉下来，这时候不用拍照
    time.sleep(2)
    camera = sensor_factory.spawn_spec_actor("camera.rgb", vehicle_transform, config.image_size, config.fov, offset)
    camera_semantic_segmentation = processor.add_camera_return_seman_camera(camera)
    
    # 创建一个字典来存储图像，按键是时间戳
    image_buffer = {}
    
    # 定义同步回调函数
    def sync_callback(image, queue_type):
        timestamp = image.timestamp
        # 将图像存储在缓冲区中
        if timestamp not in image_buffer:
            image_buffer[timestamp] = {}
        
        # 如果是RGB图像，同时收集车辆状态信息
        if queue_type == 'rgb':
            # 拍照瞬间：记录相机位置（拍照时的位置，而非处理时）
            camera_pos = camera.get_position_for_render()
            # 拍照瞬间：收集所有车辆的状态（transform + bounding box世界顶点）
            vehicle_states = []
            for veh in connect.world().get_actors().filter('vehicle.*'):
                # 关键：用车辆当前帧的transform计算bbox世界顶点（拍照时的位置）
                bbox_world_vertices = [v for v in veh.bounding_box.get_world_vertices(veh.get_transform())]
                vehicle_states.append({
                    'transform': veh.get_transform(),
                    'bbox_world': bbox_world_vertices
                })
            # 将RGB图像、车辆状态和相机位置一起存储
            image_buffer[timestamp]['rgb'] = (image, vehicle_states, camera_pos)
        else:
            # 语义分割图像直接存储
            image_buffer[timestamp][queue_type] = image
        
        # 检查是否拥有同一时间戳的RGB和语义分割图像
        if 'rgb' in image_buffer[timestamp] and 'semantic' in image_buffer[timestamp]:
            # 将配对的图像放入同步队列
            # 注意：这里rgb_data是一个元组 (image, vehicle_states, camera_pos)
            sync_queue.put({
                'rgb': image_buffer[timestamp]['rgb'],
                'semantic': image_buffer[timestamp]['semantic'],
                'timestamp': timestamp
            })
            # 从缓冲区中删除已处理的时间戳
            del image_buffer[timestamp]
            
            # 清理旧的时间戳以防止内存泄漏
            old_timestamps = [ts for ts in image_buffer.keys() if ts < timestamp - 1.0]
            for old_ts in old_timestamps:
                del image_buffer[old_ts]
    
    # listen是每次获取到图片就把图片传到()中的函数里并调用
    camera.actor.listen(lambda image: sync_callback(image, 'rgb'))
    camera_semantic_segmentation.actor.listen(lambda image: sync_callback(image, 'semantic'))

    camera.clear_picture_queue()
    camera_semantic_segmentation.clear_picture_queue()
    flag = 0
    for i in range(config.dataset_generate_image_num):
        # offset = generate_random_offset(config)
        # camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
        # processor.add_camera(camera)
        if sync_queue.qsize() > config.dataset_generate_image_num:
            if flag == 0:
                camera.actor.stop()
                camera_semantic_segmentation.actor.stop()
                flag = 1
        # 这是干啥的来着？？
        time.sleep(config.dataset_generate_interval)
        
        # 从同步队列中获取配对的图像
        if not sync_queue.empty():
            image_pair = sync_queue.get()
            # 处理配对的图像
            # 从image_pair['rgb']元组中提取数据
            rgb_image_data, vehicle_states, camera_pos = image_pair['rgb']
            image, semantic_segmentation, labels, position = processor.process_sync_images(
                (None, rgb_image_data, vehicle_states, camera_pos), image_pair['semantic'])
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