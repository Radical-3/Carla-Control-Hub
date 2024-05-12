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

    def remove_camera(self):
        self.__camera = None
        self.__sensor_factory.destroy_actor(self.__camera_semantic_segmentation)
        self.__camera_semantic_segmentation = None
        self.__projection_matricx = None

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

    def destroy(self):
        self.__sensor_factory.clear_factory()
        logger.debug("destroy processor successfully")
