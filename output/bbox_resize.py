import os


def convert_bbox_format(label_dir, output_file):
    """
    将标签文件中的边界框格式从 (x1, y1, x2, y2) 转换为 (x1, y1, w, h) 格式
    
    Args:
        label_dir: 包含标签文件的目录路径
        output_file: 输出文件路径 (groundtruth.txt)
    """
    # 获取所有标签文件
    label_files = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
    
    # 按文件名排序以确保顺序一致
    label_files.sort()
    
    # 用于记录空标签文件
    empty_files = []
    
    with open(output_file, 'w') as out_f:
        for label_file in label_files:
            label_path = os.path.join(label_dir, label_file)
            
            # 从文件名提取基础名称（不包含扩展名）
            base_name = os.path.splitext(label_file)[0]
            
            # 读取文件内容
            with open(label_path, 'r') as in_f:
                lines = in_f.readlines()
                
            # 检查是否为空文件
            if not lines or all(line.strip() == '' for line in lines):
                empty_files.append(label_file)
                continue
                
            # 处理每一行
            for line in lines:
                coords = list(map(float, line.strip().split()))
                if len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    # 转换为 (x1, y1, w, h) 格式
                    w = x2 - x1
                    h = y2 - y1
                    
                    # 写入 groundtruth.txt，格式为: filename,x1,y1,w,h
                    out_f.write(f"{int(x1)},{int(y1)},{int(w)},{int(h)}\n")
    
    print(f"转换完成，共处理 {len(label_files) - len(empty_files)} 个标签文件")
    print(f"结果已保存至: {output_file}")
    
    # 输出空标签文件信息
    if empty_files:
        print(f"发现 {len(empty_files)} 个空标签文件:")
        for empty_file in empty_files:
            print(f"  - {empty_file}")
    
    return empty_files


if __name__ == "__main__":
    # 示例用法
    label_directory = "./ostrack2/label"  # 标签文件目录
    output_path = "./ostrack2/ostrack_bbox/groundtruth.txt"  # 输出文件路径
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(label_directory):
        empty_files = convert_bbox_format(label_directory, output_path)
    else:
        print(f"标签目录不存在: {label_directory}")