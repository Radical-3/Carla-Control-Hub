import random
import numpy as np


def generate_random_offset(config):
    if config.dataset_generate_use_radius:
        phi = np.random.uniform(0, 2 * np.pi)
        theta = np.random.uniform(0, np.pi / 2)  # 限制 theta 角度范围在 [0, pi/2] 内,使 z 恒正
        r = config.dataset_generate_radius

        # 将球面坐标转换为笛卡尔坐标
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
    else:
        x = random.uniform(-config.dataset_generate_offset_x, config.dataset_generate_offset_x)
        y = random.uniform(-config.dataset_generate_offset_y, config.dataset_generate_offset_y)
        z = config.height
    return x, y, z


def generate_specify_offset(config):
    # return -10, 0, 10
    return 0, 10, 10

def generate_series_offset(config):
    theta = np.linspace(0, 2 * np.pi, config.visual_assessment_camera_num, endpoint=False)
    phi = np.arccos(config.visual_assessment_height / config.visual_assessment_radius)  # 垂直角度

    points = [[
        config.visual_assessment_radius * np.sin(phi) * np.cos(t),
        config.visual_assessment_radius * np.sin(phi) * np.sin(t),
        config.visual_assessment_radius * np.cos(phi)
    ] for t in theta]
    return points
