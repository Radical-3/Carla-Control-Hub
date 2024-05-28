# Carla Control Hub

基于carla的自动驾驶仿真模拟器的外接控制程序

## Introduction

本项目为基于carla的自动驾驶仿真模拟器的外接操作控制程序,使用carla提供python API对carla模拟器进行指定的操作。
目前主要支持的功能有：

- 地图选择
- 环境选择
- 车辆生成
- 传感器生成
- 传感器数据计算与标注
- 传感器数据导出保存
- 打包数据集



## Installation

1. 项目基于Carla 0.9.15版本，安装教程及下载地址请参考[Carla官网](https://carla.org/)
2. 使用git克隆本项目，或者在当前页面直接下载zip文件
    ```shell
    git clone
    ```
3. 本项目基于Python3.10.14开发，使用如下命令确认python版本，以及安装依赖包
    ```shell
    python --version
    ```
4. 安装项目的总依赖包
   ```shell
    pip install -r requirements.txt
    ```

## Usage

1. 项目中的方法已经集成到method包中，通过对外暴露接口`test_script.py`统一调用。
    ```shell
    python test_script.py
    ```
2. 修改配置文件base.yaml中可以直接改变生成的数据集的参数 例如： 修改base.yaml中的dataset_generate_image_num参数可以改变生成的数据集的大小
3. 生成的数据集会保存在output文件夹中

## Contributing

本项目由[@黑羽彻](https://github.com/ZhaoZhiqiao)
管理、 [@Caesar545](https://github.com/Caesar545)、[@He Fasheng](https://github.com/clown001)协同开发。  
若项目存在任何问题，欢迎提交issue或pull requests，也可以直接通过邮箱联系[@黑羽彻](https://github.com/ZhaoZhiqiao):
zhao_zhiqiao@outlook.com。

## License

本项目为非开源的私有项目，未经允许禁止转载
