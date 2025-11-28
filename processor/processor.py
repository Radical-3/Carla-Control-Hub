from log import logger

import numpy as np
from factory import Sensor_Factory
from .utils import generate_colors, build_projection_matrix, camera_location_to_image_location


class Processor:
    def __init__(self, config, connect):
        self.__world = connect.world()
        self.__color = generate_colors()
        self.__sensor_factory = Sensor_Factory(connect)

        self.__camera = None
        self.__camera_semantic_segmentation = None
        self.__projection_matricx = None

        self.__city_object_labels = config.city_object_labels

    def add_camera(self, camera):
        self.__camera = camera
        attach, image_size, fov, offset = camera.get_parameters()
        self.__projection_matricx = build_projection_matrix(image_size[0], image_size[1], fov)
        self.__camera_semantic_segmentation = self.__sensor_factory.spawn_actor('camera.semantic_segmentation',
                                                                                attach,
                                                                                image_size,
                                                                                fov,
                                                                                offset)

    def add_camera_return_seman_camera(self, camera):
        self.__camera = camera
        vehicle_transform, image_size, fov, offset = camera.new_get_parameters()
        self.__projection_matricx = build_projection_matrix(image_size[0], image_size[1], fov)
        self.__camera_semantic_segmentation = self.__sensor_factory.spawn_spec_actor('camera.semantic_segmentation',
                                                                                vehicle_transform,
                                                                                image_size,
                                                                                fov,
                                                                                offset)
        return self.__camera_semantic_segmentation

    def remove_camera(self):
        self.__camera = None
        self.__sensor_factory.destroy_actor(self.__camera_semantic_segmentation)
        self.__camera_semantic_segmentation = None
        self.__projection_matricx = None

    def get_picture_que(self, img_queue):
        image = None
        while True:
            if img_queue.empty():
                continue
            else:
                image = img_queue.get()
                break
        return np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

    def listen_rgb(self, image, queue):
        # 拍照瞬间：记录相机位置（拍照时的位置，而非处理时）
        camera_pos = self.__camera.get_position_for_render()
        # 拍照瞬间：收集所有车辆的状态（transform + bounding box世界顶点）
        vehicle_states = []
        for veh in self.__world.get_actors().filter('vehicle.*'):
            # 关键：用车辆当前帧的transform计算bbox世界顶点（拍照时的位置）
            bbox_world_vertices = [v for v in veh.bounding_box.get_world_vertices(veh.get_transform())]
            vehicle_states.append({
                'transform': veh.get_transform(),
                'bbox_world': bbox_world_vertices
            })
        # 把“rgb图、车辆状态、相机位置”存入队列（语义图后续会和rgb图匹配帧）
        queue.put(('rgb', image, vehicle_states, camera_pos))

    def process_queue(self, camera_queue, semantic_queue):
        if self.__camera is None:
            logger.error("No camera")
            return None

        # 从队列中获取数据
        _, image_raw, vehicle_states, position = camera_queue.get()
        semantic_segmentation = self.get_picture_que(semantic_queue)

        # 转换图像数据
        image = np.reshape(np.copy(image_raw.raw_data), (image_raw.height, image_raw.width, 4))

        world_to_camera_matrix = np.array(self.__camera.get_inverse_matrix())

        labels = list()
        # 处理每辆车的状态
        for vehicle_state in vehicle_states:
            coordinates = list()
            # 使用同步的边界框顶点
            for point in vehicle_state['bbox_world']:
                coordinates.append(camera_location_to_image_location(point,
                                                                     self.__projection_matricx,
                                                                     world_to_camera_matrix))

            coordinates = np.array(coordinates, dtype=np.int16)
            center = np.mean(coordinates, axis=0, dtype=np.int16)[::-1]
            left_top = np.min(coordinates, axis=0).astype(np.int16)
            right_bottom = np.max(coordinates, axis=0).astype(np.int16)

            if 0 < center[0] < image.shape[0] and 0 < center[1] < image.shape[1]:
                B, G, R, A = semantic_segmentation[center[0], center[1]]
                if R in self.__city_object_labels:
                    labels.append([left_top[0], left_top[1], right_bottom[0], right_bottom[1]])

        return image, semantic_segmentation, labels, position
    # def process_queue(self, camera_queue, semantic_queue):
    #     if self.__camera is None:
    #         logger.error("No camera")
    #         return None
    #
    #     world_to_camera_matrix = np.array(self.__camera.get_inverse_matrix())
    #     position = self.__camera.get_position_for_render()
    #
    #     # self.__camera.clear_picture_queue()
    #     # self.__camera_semantic_segmentation.clear_picture_queue()
    #
    #     image = self.get_picture_que(camera_queue)
    #     semantic_segmentation = self.get_picture_que(semantic_queue)
    #     # image = self.__camera.get_picture()
    #     # semantic_segmentation = self.__camera_semantic_segmentation.get_picture()
    #
    #     labels = list()
    #     for vehicle in self.__world.get_actors().filter('vehicle.*'):
    #         coordinates = list()
    #         bounding_box = vehicle.bounding_box
    #         # 将车辆边界框在世界坐标系下的顶点坐标存储在 points 列表中
    #         points = [vertex for vertex in bounding_box.get_world_vertices(vehicle.get_transform())]
    #         # 将车辆边界框顶点从世界坐标系转换为相机坐标系，然后将相机坐标系下的点转换为图像坐标系下的点，并将转换后的坐标存储在 coordinates 列表中
    #         for point in points:
    #             coordinates.append(camera_location_to_image_location(point,
    #                                                                  self.__projection_matricx,
    #                                                                  world_to_camera_matrix))
    #
    #         coordinates = np.array(coordinates, dtype=np.int16)
    #         center = np.mean(coordinates, axis=0, dtype=np.int16)[::-1]
    #         left_top = np.min(coordinates, axis=0).astype(np.int16)
    #         right_bottom = np.max(coordinates, axis=0).astype(np.int16)
    #
    #         if 0 < center[0] < image.shape[0] and 0 < center[1] < image.shape[1]:
    #             B, G, R, A = semantic_segmentation[center[0], center[1]]
    #             if R in self.__city_object_labels:
    #                 labels.append([left_top[0], left_top[1], right_bottom[0], right_bottom[1]])
    #     return image, semantic_segmentation, labels, position

    def process(self):
        if self.__camera is None:
            logger.error("No camera")
            return None

        world_to_camera_matrix = np.array(self.__camera.get_inverse_matrix())
        position = self.__camera.get_position_for_render()

        self.__camera.clear_picture_queue()
        self.__camera_semantic_segmentation.clear_picture_queue()

        image = self.__camera.get_picture()
        semantic_segmentation = self.__camera_semantic_segmentation.get_picture()

        labels = list()
        for vehicle in self.__world.get_actors().filter('vehicle.*'):
            coordinates = list()
            bounding_box = vehicle.bounding_box
            # 将车辆边界框在世界坐标系下的顶点坐标存储在 points 列表中
            points = [vertex for vertex in bounding_box.get_world_vertices(vehicle.get_transform())]
            # 将车辆边界框顶点从世界坐标系转换为相机坐标系，然后将相机坐标系下的点转换为图像坐标系下的点，并将转换后的坐标存储在 coordinates 列表中
            for point in points:
                coordinates.append(camera_location_to_image_location(point,
                                                                     self.__projection_matricx,
                                                                     world_to_camera_matrix))

            coordinates = np.array(coordinates, dtype=np.int16)
            center = np.mean(coordinates, axis=0, dtype=np.int16)[::-1]
            left_top = np.min(coordinates, axis=0).astype(np.int16)
            right_bottom = np.max(coordinates, axis=0).astype(np.int16)

            if 0 < center[0] < image.shape[0] and 0 < center[1] < image.shape[1]:
                B, G, R, A = semantic_segmentation[center[0], center[1]]
                if R in self.__city_object_labels:
                    labels.append([left_top[0], left_top[1], right_bottom[0], right_bottom[1]])
        return image, semantic_segmentation, labels, position

    def process_new(self):
        if self.__camera is None:
            logger.error("No camera")
            return None

        world_to_camera_matrix = np.array(self.__camera.get_inverse_matrix())
        position = self.__camera.get_position_for_render()

        # self.__camera.clear_picture_queue()
        # self.__camera_semantic_segmentation.clear_picture_queue()
        self.__camera.enough_images()
        image = self.__camera.get_picture()
        semantic_segmentation = self.__camera_semantic_segmentation.get_picture()

        labels = list()
        for vehicle in self.__world.get_actors().filter('vehicle.*'):
            coordinates = list()
            bounding_box = vehicle.bounding_box
            # 将车辆边界框在世界坐标系下的顶点坐标存储在 points 列表中
            points = [vertex for vertex in bounding_box.get_world_vertices(vehicle.get_transform())]
            # 将车辆边界框顶点从世界坐标系转换为相机坐标系，然后将相机坐标系下的点转换为图像坐标系下的点，并将转换后的坐标存储在 coordinates 列表中
            for point in points:
                coordinates.append(camera_location_to_image_location(point,
                                                                     self.__projection_matricx,
                                                                     world_to_camera_matrix))

            coordinates = np.array(coordinates, dtype=np.int16)
            center = np.mean(coordinates, axis=0, dtype=np.int16)[::-1]
            left_top = np.min(coordinates, axis=0).astype(np.int16)
            right_bottom = np.max(coordinates, axis=0).astype(np.int16)

            if 0 < center[0] < image.shape[0] and 0 < center[1] < image.shape[1]:
                B, G, R, A = semantic_segmentation[center[0], center[1]]
                if R in self.__city_object_labels:
                    labels.append([left_top[0], left_top[1], right_bottom[0], right_bottom[1]])
        return image, semantic_segmentation, labels, position

    def process_continue(self):
        if self.__camera is None:
            logger.error("No camera")
            return None

        world_to_camera_matrix = np.array(self.__camera.get_inverse_matrix())
        position = self.__camera.get_position_for_render()

        # self.__camera.clear_picture_queue()
        # self.__camera_semantic_segmentation.clear_picture_queue()

        image = self.__camera.get_picture()
        semantic_segmentation = self.__camera_semantic_segmentation.get_picture()

        labels = list()
        for vehicle in self.__world.get_actors().filter('vehicle.*'):
            coordinates = list()
            bounding_box = vehicle.bounding_box
            # 将车辆边界框在世界坐标系下的顶点坐标存储在 points 列表中
            points = [vertex for vertex in bounding_box.get_world_vertices(vehicle.get_transform())]
            # 将车辆边界框顶点从世界坐标系转换为相机坐标系，然后将相机坐标系下的点转换为图像坐标系下的点，并将转换后的坐标存储在 coordinates 列表中
            for point in points:
                coordinates.append(camera_location_to_image_location(point,
                                                                     self.__projection_matricx,
                                                                     world_to_camera_matrix))

            coordinates = np.array(coordinates, dtype=np.int16)
            center = np.mean(coordinates, axis=0, dtype=np.int16)[::-1]
            left_top = np.min(coordinates, axis=0).astype(np.int16)
            right_bottom = np.max(coordinates, axis=0).astype(np.int16)

            if 0 < center[0] < image.shape[0] and 0 < center[1] < image.shape[1]:
                B, G, R, A = semantic_segmentation[center[0], center[1]]
                if R in self.__city_object_labels:
                    labels.append([left_top[0], left_top[1], right_bottom[0], right_bottom[1]])
        return image, semantic_segmentation, labels, position

    def process_sync_images(self, rgb_image_data, semantic_image_data):
        """
        处理同步的RGB图像和语义分割图像
        
        Args:
            rgb_image_data: 包含RGB图像和车辆状态的元组 ('rgb', image, vehicle_states, position)
            semantic_image_data: 语义分割图像数据
            
        Returns:
            tuple: (image, semantic_segmentation, labels, position)
        """
        if self.__camera is None:
            logger.error("No camera")
            return None

        # 解析RGB图像数据
        _, image_raw, vehicle_states, position = rgb_image_data
        
        # 转换图像数据
        image = np.reshape(np.copy(image_raw.raw_data), (image_raw.height, image_raw.width, 4))
        semantic_segmentation = np.reshape(np.copy(semantic_image_data.raw_data), 
                                         (semantic_image_data.height, semantic_image_data.width, 4))

        world_to_camera_matrix = np.array(self.__camera.get_inverse_matrix())

        labels = list()
        # 处理每辆车的状态
        for vehicle_state in vehicle_states:
            coordinates = list()
            # 使用同步的边界框顶点
            for point in vehicle_state['bbox_world']:
                coordinates.append(camera_location_to_image_location(point,
                                                                 self.__projection_matricx,
                                                                 world_to_camera_matrix))

            coordinates = np.array(coordinates, dtype=np.int16)
            center = np.mean(coordinates, axis=0, dtype=np.int16)[::-1]
            left_top = np.min(coordinates, axis=0).astype(np.int16)
            right_bottom = np.max(coordinates, axis=0).astype(np.int16)

            if 0 < center[0] < image.shape[0] and 0 < center[1] < image.shape[1]:
                B, G, R, A = semantic_segmentation[center[0], center[1]]
                if R in self.__city_object_labels:
                    labels.append([left_top[0], left_top[1], right_bottom[0], right_bottom[1]])

        return image, semantic_segmentation, labels, position

    def destroy(self):
        self.__sensor_factory.clear_factory()
        logger.debug("destroy processor successfully")
