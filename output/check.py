import cv2
import os
import numpy as np


def draw_bboxes(image_path, label_path):
    """
    在图片上绘制边界框

    Args:
        image_path: 图片文件路径
        label_path: 标签文件路径
    """
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图片: {image_path}")
        return None

    # 读取标签文件
    bboxes = []
    if os.path.exists(label_path):
        with open(label_path, 'r') as f:
            for line in f.readlines():
                # 解析每行的bbox坐标 [x1, y1, x2, y2]
                coords = list(map(float, line.strip().split()))
                if len(coords) == 4:
                    bboxes.append([int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])])

    # 在图片上绘制边界框
    for bbox in bboxes:
        x1, y1, x2, y2 = bbox
        # 绘制矩形框 (蓝色)
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # 在边界框左上角添加标签
        cv2.putText(image, 'car', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    return image


def draw_single_bbox(image, bbox):
    """
    在图片上绘制单个边界框
    
    Args:
        image: 图片数组
        bbox: 边界框坐标 [x1, y1, w, h]
        
    Returns:
        绘制了边界框的图片
    """
    x1, y1, w, h = bbox
    x2 = x1 + w
    y2 = y1 + h
    
    # 绘制矩形框 (蓝色)
    cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
    
    # 在边界框左上角添加标签
    cv2.putText(image, 'car', (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    
    return image


def show_image_with_bbox(image_path, bbox):
    """
    展示图片并绘制边界框
    
    Args:
        image_path: 图片路径
        bbox: 边界框坐标 [x1, y1, w, h]
    """
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图片: {image_path}")
        return
    
    # 绘制边界框
    image_with_bbox = draw_single_bbox(image.copy(), bbox)
    
    # 调整图片大小以便更好地显示
    height, width = image_with_bbox.shape[:2]
    max_height = 800
    if height > max_height:
        scale = max_height / height
        new_width = int(width * scale)
        new_height = int(height * scale)
        image_with_bbox = cv2.resize(image_with_bbox, (new_width, new_height))
    
    # 显示图片
    window_name = f'Image with bbox: {os.path.basename(image_path)}'
    cv2.imshow(window_name, image_with_bbox)
    
    print(f"显示图片: {image_path}")
    print(f"边界框坐标: x1={bbox[0]}, y1={bbox[1]}, w={bbox[2]}, h={bbox[3]}")
    print("按任意键关闭窗口...")
    
    # 等待按键
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def check_dataset(image_dir, label_dir):
    """
    检查数据集中的图片和对应的标签

    Args:
        image_dir: 图片目录路径
        label_dir: 标签目录路径
    """
    # 获取所有图片文件并按名称排序以确保顺序展示
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    
    if not image_files:
        print("未找到任何PNG图片文件")
        return

    print(f"找到 {len(image_files)} 个图片文件")

    for i, image_file in enumerate(image_files):
        # 构建对应的文件名
        base_name = os.path.splitext(image_file)[0]
        label_file = base_name + '.txt'

        image_path = os.path.join(image_dir, image_file)
        label_path = os.path.join(label_dir, label_file)

        # 绘制带有边界框的图片
        image_with_boxes = draw_bboxes(image_path, label_path)

        if image_with_boxes is not None:
            # 调整图片大小以便更好地显示
            height, width = image_with_boxes.shape[:2]
            max_height = 800
            if height > max_height:
                scale = max_height / height
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_with_boxes = cv2.resize(image_with_boxes, (new_width, new_height))

            # 显示图片
            window_name = f'Image {i+1}/{len(image_files)}: {image_file}'
            cv2.imshow(window_name, image_with_boxes)

            print(f"显示图片 ({i+1}/{len(image_files)}): {image_file}")
            print(f"对应标签: {label_file}")
            print("按任意键继续到下一张图片，按 'q' 键退出...")
            
            # 等待按键
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                break

            # 关闭当前窗口
            cv2.destroyWindow(window_name)
        else:
            print(f"无法处理图片: {image_file}")
            
    print("检查完成!")


if __name__ == "__main__":
    # 示例用法
    # 请根据实际情况修改这两个路径
    # image_directory = "./ostrack2/image"
    # label_directory = "./ostrack2/label"
    #
    # if os.path.exists(image_directory) and os.path.exists(label_directory):
    #     check_dataset(image_directory, label_directory)
    # else:
    #     print("请提供有效的图片和标签目录路径")
    #     print("使用方法:")
    #     print("check_dataset('你的图片目录路径', '你的标签目录路径')")

    show_image_with_bbox("./check_ostrack_train_bbox/00000001.jpg", [395,340,532,407])