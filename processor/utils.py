import random
import numpy as np


# 得到相机的投影矩阵，作用是将三维物体在相机坐标系中的位置投影到图像平面上
def build_projection_matrix(height, width, fov):
    # 计算得到相机的焦距focal
    focal = width / (2.0 * np.tan(fov * np.pi / 360.0))
    # 创建了一个3*3的单位矩阵
    matrix = np.identity(3)
    # 对K矩阵进行变换，可以在后续的计算或操作中使用 matrix 矩阵来表示相机的内参矩阵，其中包括焦距、光学中心以及图像的尺寸信息。
    # 确保 matrix 矩阵在相机的内参矩阵中具有正确的焦距值。
    matrix[0, 0] = matrix[1, 1] = focal
    # 将图像的中心位置与相机的光学中心对齐。
    matrix[0, 2] = width / 2.0
    # 将图像的中心位置与相机的光学中心对齐。
    matrix[1, 2] = height / 2.0
    return matrix


# 将相机的坐标系变换到图片坐标系,完成摄像机拍摄的世界坐标到图片坐标的变换
def camera_location_to_image_location(loc, matrix, w2c):
    # 计算三维坐标的二维投影
    # 格式化输入坐标（loc 是一个 carla.Position 对象）
    point = np.array([loc.x, loc.y, loc.z, 1])
    # 转换到相机坐标系
    point_camera = np.dot(w2c, point)
    # 将坐标系从 UE4 的坐标系转换为标准坐标系（y, -z, x），同时移除第四个分量
    point_camera = [point_camera[1], -point_camera[2], point_camera[0]]
    # 使用相机矩阵进行三维到二维投影
    point_img = np.dot(matrix, point_camera)
    # 归一化
    point_img[0] /= point_img[2]
    point_img[1] /= point_img[2]
    return point_img[0], point_img[1]


def get_detect_result():
    x1 = random.randint(-20, 20)
    x2 = random.randint(-20, 20)
    x3 = random.randint(-20, 20)
    x4 = random.randint(-20, 20)
    x5 = random.randint(-20, 20)
    x6 = random.randint(-20, 20)
    x7 = random.randint(-20, 20)
    x8 = random.randint(-20, 20)
    x9 = random.uniform(-0.1, 0.1)
    x10 = random.uniform(-0.1, 0.1)
    return {"yolov5": [["car", 0.8 + x9, [743 + x1, 441 + x2, 1303 + x3, 683 + x4]]],
            "yolov6": [["car", 0.8 + x10, [743 + x5, 441 + x6, 1303 + x7, 683 + x8]]]}


def generate_colors():
    hex_color = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB',
                 '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
    palette = []
    for item in hex_color:
        h = '#' + item
        palette.append(tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4)))
    return palette
