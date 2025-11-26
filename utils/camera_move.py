import math
import random

import carla


def move_camera_with_jitter(camera, time_step):
    current_transform = camera.actor.get_transform()

    # 使用正弦函数生成小幅抖动
    jitter_x = math.sin(time_step) * 0.05  # x方向小幅度抖动
    jitter_y = math.cos(time_step) * 0.05  # y方向小幅度抖动
    jitter_z = math.sin(time_step) * 0.02  # z方向小幅度抖动

    new_location = carla.Location(
        x=current_transform.location.x + jitter_x,
        y=current_transform.location.y + jitter_y,
        z=current_transform.location.z + jitter_z
    )

    new_transform = carla.Transform(new_location, current_transform.rotation)
    camera.actor.set_transform(new_transform)
    time_step += 0.1


def move_camera_with_noise(camera):
    current_transform = camera.actor.get_transform()

    # 使用高斯噪声模拟抖动
    jitter_x = random.gauss(0, 0.03)  # x方向的小幅随机抖动
    jitter_y = random.gauss(0, 0.03)  # y方向的小幅随机抖动
    jitter_z = random.gauss(0, 0.02)  # z方向的小幅随机抖动

    new_location = carla.Location(
        x=current_transform.location.x + jitter_x,
        y=current_transform.location.y + jitter_y,
        z=current_transform.location.z + jitter_z
    )

    new_transform = carla.Transform(new_location, current_transform.rotation)
    camera.actor.set_transform(new_transform)
