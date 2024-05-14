import logging
import os

import cv2
import numpy as np
from tqdm import tqdm


# 文件的一致性检测函数
def consistency_check(config):
    # 读取数据集路径并分别获得图片、掩码、相机、标签路径
    path = os.path.join(str(config.dataset_path), str(config.dataset_name))
    image_path = os.path.join(path, "image")
    mask_path = os.path.join(path, "mask")
    camera_position_path = os.path.join(path, "camera_position")
    label_path = os.path.join(path, "label")
    # 遍历每个物体的四个文件，如果每个物体的四个文件都存在，则继续执行，否则抛出异常
    for file_path in tqdm(os.listdir(image_path), desc="Consistency Check: "):
        if file_path.split(".")[-1] in ["png", "jpg"]:
            identifier = file_path.split(".")[0]
            flag = [True, True, True]
            flag[0] = os.path.exists(os.path.join(mask_path, f"{identifier}.png"))
            flag[1] = os.path.exists(os.path.join(camera_position_path, f"{identifier}.txt"))
            flag[2] = os.path.exists(os.path.join(label_path, f"{identifier}.txt"))
            if all(flag):
                continue
            else:
                logging.error(f"id:{identifier} is not consistency")
                logging.error(f"mask exist:{flag[0]}, camera_position exist:{flag[1]}, label exist:{flag[2]}")
                raise Exception(f"Image {identifier} is not consistent")


# 因为神经渲染器的结果是正方形图片，需要对Carla成像进行修建
def cut_images_to_square(config):
    # 检索图片后缀格式,并将其保存在列表中
    path = os.path.join(str(config.dataset_path), str(config.dataset_name))
    image_path = os.path.join(path, "image")
    semantic_segmentation_path = os.path.join(path, "semantic_segmentation")

    # 初始化图像路径和语义分割路径列表
    images = list()
    semantic_segmentation_paths = list()
    # 遍历image_path下的文件，如果文件是以png或者jpg结尾，则将文件名字加到images中
    for file_path in os.listdir(image_path):
        # 如果文件是以png或者jpg结尾，则将文件名字加到images中
        if file_path.split(".")[-1] in ["png", "jpg"]:
            images.append(file_path)

    # 使用 tqdm 库中的进度条来遍历一个图像文件列表，并将图像裁剪为正方形。裁剪后的图像将覆盖原始文件。
    for file_path in tqdm(images, desc="Cut Images To Square: "):
        mask = cv2.imread(os.path.join(image_path, file_path))
        height = mask.shape[0]
        width = mask.shape[1]
        if height > width:
            cut_value = (height - width) // 2
            mask = mask[cut_value: (height - cut_value), :]
        else:
            cut_value = (width - height) // 2
            mask = mask[:, cut_value:(width - cut_value)]
        cv2.imwrite(os.path.join(image_path, file_path), mask)

    # 遍历semantic_segmentation_path下的文件，如果文件是以png或者jpg结尾，则将文件名字加到semantic_segmentation_paths中
    for file_path in os.listdir(semantic_segmentation_path):
        if file_path.split(".")[-1] in ["png", "jpg"]:
            semantic_segmentation_paths.append(file_path)

    # 使用 tqdm 库中的进度条来遍历一个图像文件列表，并将图像裁剪为正方形。裁剪后的图像将覆盖原始文件。
    for file_path in tqdm(semantic_segmentation_paths, desc="Cut Semantic_Segmentation To Square: "):
        # 读取图片
        mask = cv2.imread(os.path.join(semantic_segmentation_path, file_path))
        height = mask.shape[0]
        width = mask.shape[1]
        if height > width:
            cut_value = (height - width) // 2
            mask = mask[cut_value: (height - cut_value), :]
        else:
            cut_value = (width - height) // 2
            mask = mask[:, cut_value:(width - cut_value)]
        cv2.imwrite(os.path.join(semantic_segmentation_path, file_path), mask)


# 遍历label(物体几何坐标)文件夹，读取每个文件的内容，调整坐标为新的正方形坐标，并将调整后的坐标写回原始文件。
def cut_images_label_to_square(config):
    path = os.path.join(str(config.dataset_path), str(config.dataset_name))
    # 得到要裁剪的label的path
    label_path = os.path.join(path, "label")
    original_size = config.image_size
    new_size = [min(config.image_size)] * 2
    crop_amount = [0, 0]
    # 得到要裁剪的长度和宽度
    crop_amount[0] = (original_size[0] - new_size[0]) // 2
    crop_amount[1] = (original_size[1] - new_size[1]) // 2

    # 检索图片后缀格式,找到存储物体四个角的坐标的文件，并将其保存在列表中
    labels = list()
    for file_path in os.listdir(label_path):
        if file_path.split(".")[-1] in ["txt"]:
            labels.append(file_path)
    # 遍历指定文件夹路径
    for file_path in tqdm(labels, desc="Cut Picture Label To Square: "):
        # 读取图片
        with open(os.path.join(label_path, file_path), "r") as f:
            line = list(map(float, f.readline().strip().split()))
            if len(line) < 4:
                continue
            line[0] -= crop_amount[0]
            line[1] -= crop_amount[1]
            line[2] -= crop_amount[0]
            line[3] -= crop_amount[1]
            line = list(map(int, line))
        with open(os.path.join(label_path, file_path), "w") as f:
            f.write(f"{line[0]} {line[1]} {line[2]} {line[3]}")


# 将遍历指定的语义分割图像文件夹，读取每个图像文件，将图像转换为黑白掩码图像，并将转换后的图像保存回原始文件。
# 最后，将语义分割图像文件夹重命名为 "mask"。
def semantic_segmentation_to_mask(config):
    path = os.path.join(str(config.dataset_path), str(config.dataset_name))
    semantic_segmentation_path = os.path.join(path, "semantic_segmentation")
    city_object_labels = config.city_object_labels

    # 检索图片后缀格式,并将其保存在列表中
    semantic_segmentations = list()
    for file_path in os.listdir(semantic_segmentation_path):
        if file_path.split(".")[-1] in ["png", "jpg"]:
            semantic_segmentations.append(file_path)

    # 遍历指定文件夹路径
    for filePath in tqdm(semantic_segmentations, desc="Semantic Segmentation To Mask: "):
        # 读取图片
        semantic_segmentation = cv2.imread(os.path.join(semantic_segmentation_path, filePath))
        # 遍历图片的每一个像素,生成一个和semantic_segmentation大小相同的掩码矩阵，如果semantic_segmentation的指定的元素包含在city_object_labels中，则为True
        mask = np.isin(semantic_segmentation[:, :, 2], city_object_labels)
        # 根据掩码矩阵，true为黑，false为白，生成一个黑白图像
        black_white_image = np.where(mask, 255, 0)

        # 删除原始的图像，并将修改后的黑白图像添加到里面
        os.remove(os.path.join(semantic_segmentation_path, filePath))
        cv2.imwrite(os.path.join(semantic_segmentation_path, filePath), black_white_image)
    # 将语义分割图像文件夹重新命名为mask文件夹
    mask_path = semantic_segmentation_path.replace(os.path.split(semantic_segmentation_path)[1], "mask")
    os.rename(semantic_segmentation_path, mask_path)


# 文件打包函数
def packing(config):
    # 读取图片，掩码，相机，标签路径，生成打包后的文件夹路径
    path = os.path.join(str(config.dataset_path), str(config.dataset_name))

    image_path = os.path.join(path, "image")
    mask_path = os.path.join(path, "mask")
    camera_position_path = os.path.join(path, "camera_position")
    label_path = os.path.join(path, "label")
    package_path = os.path.join(path, "package")
    # 生成打包后的文件夹
    os.makedirs(package_path, exist_ok=True)
    # 遍历每个物体的四个文件
    for file_path in tqdm(os.listdir(image_path), desc="packing: "):
        if file_path.split(".")[-1] in ["png", "jpg"]:
            identifier = file_path.split(".")[0]
            # 读取物体的图片，转换图片格式并归一化
            image = cv2.cvtColor(cv2.imread(os.path.join(image_path, file_path)), cv2.COLOR_BGR2RGB)
            # 读取掩码的图片，转换图片格式并归一化
            mask = cv2.cvtColor(cv2.imread(os.path.join(mask_path, f"{identifier}.png")), cv2.COLOR_BGR2RGB) / 255
            # 读取相机坐标
            with open(os.path.join(camera_position_path, f"{identifier}.txt"), "r") as f:
                camera_position = f.readline().split()
            # 读取标签
            with open(os.path.join(label_path, f"{identifier}.txt"), "r") as f:
                label = f.readline().split()
            # 转换格式
            identifier = np.array(identifier, dtype=np.uint32)
            image = np.array(image, dtype=np.uint8)
            mask = np.array(mask, dtype=np.uint8)
            label = np.array(label, dtype=np.int16)
            camera_position = np.array(camera_position, dtype=np.float32)
            # 打包，将同一物体的名称，图片，掩码，对应相机位置，标签放在同一个数组中
            package = np.array([identifier, image, mask, label, camera_position], dtype=object)
            # 保存
            np.save(os.path.join(package_path, rf"{int(identifier)}"), package)
