import math
import queue

import carla
import numpy as np

from actor.base_actor import Base_Actor


class Camera(Base_Actor):
    def __init__(self, world, blueprint, vehicle_transform, image_size, fov, offset, actor_id=None):
        super().__init__(world)
        self.__vehicle_transform = vehicle_transform
        self.__image_height = image_size[0]
        self.__image_width = image_size[1]
        self.__fov = fov

        self.__offset_x = offset[0]
        self.__offset_y = offset[1]
        self.__offset_z = offset[2]
        self.__camera_transform = None
        self.__image_queue = queue.Queue()

        if actor_id is not None:
            self.actor = self._world.get_actor(actor_id)
        else:
            blueprint.set_attribute('image_size_x', f"{self.__image_width}")
            blueprint.set_attribute('image_size_y', f"{self.__image_height}")

            pitch = math.degrees(math.atan2(-self.__offset_z, math.sqrt(self.__offset_x ** 2 + self.__offset_y ** 2)))
            yaw = math.degrees(math.atan2(-self.__offset_y, -self.__offset_x))
            # yaw = math.degrees(math.atan2(-self.__offset_y, -self.__offset_x)) + 30
            roll = 0
            true_x = vehicle_transform.location.x + self.__offset_x
            true_y = vehicle_transform.location.y + self.__offset_y
            true_z = vehicle_transform.location.z + self.__offset_z
            # camera_transform = carla.Transform(carla.Location(x=self.__offset_x, y=self.__offset_y, z=self.__offset_z),
            #                                    carla.Rotation(pitch=pitch, yaw=yaw, roll=roll))
            self.__camera_transform = carla.Transform(carla.Location(x=true_x, y=true_y, z=true_z),
                                                      carla.Rotation(pitch=pitch, yaw=yaw, roll=roll))

            # self.actor = self._world.spawn_actor(blueprint, camera_transform, attach_to=self.__attach.item())
            # if self.__attach == None:
            #     self.actor = self._world.spawn_actor(blueprint, camera_transform)
            # else:
            #     self.actor = self._world.spawn_actor(blueprint, camera_transform, attach_to=self.__attach.item())
            try:
                self.actor = self._world.spawn_actor(blueprint, self.__camera_transform)
                # 先暂停一下看下面的print是不是正确的相机位置
                # 不加上这个sleep输出的位置是原点，加上的就是正确相机位置，说明有延迟，但是相机位置是没错的
                # time.sleep(1)
                # print("相机生成成功！")
                # print(f"相机最终位置: {self.actor.get_transform()}")

            except RuntimeError as e:
                print(f"相机生成失败！原因: {e}")

        if self.actor is not None:
            self._id = self.actor.id
            # self._actor.listen(self.__image_queue.put)

    def get_position_for_render(self):
        distance = math.sqrt(self.__offset_x ** 2 + self.__offset_y ** 2 + self.__offset_z ** 2)
        elevation = math.degrees(math.atan2(self.__offset_z, math.sqrt(self.__offset_x ** 2 + self.__offset_y ** 2)))
        azimuth = math.degrees(math.atan2(self.__offset_y, -self.__offset_x))
        return distance, elevation, azimuth

    def get_picture(self):
        image = None
        while True:
            if self.__image_queue.empty():
                continue
            else:
                image = self.__image_queue.get()
                break
        return np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

    def enough_images(self):
        if self.__image_queue.qsize() > 100:
            self.actor.stop()

    def get_parameters(self):
        return self.__attach, [self.__image_height, self.__image_width], self.__fov, [self.__offset_x,
                                                                                      self.__offset_y,
                                                                                      self.__offset_z]

    def new_get_parameters(self):
        return self.__vehicle_transform, [self.__image_height, self.__image_width], self.__fov, [self.__offset_x,
                                                                                                 self.__offset_y,
                                                                                                 self.__offset_z]

    def get_spatial_resolution(self):
        h = float(self.actor.get_transform().location.z)
        return 2 * h * math.atan(math.radians(self.__fov / 2)) / min(self.__image_width, self.__image_height)

    def get_inverse_matrix(self):
        return self.actor.get_transform().get_inverse_matrix()

    def clear_picture_queue(self):
        self.__image_queue.queue.clear()

    def destroy(self):
        state = False
        if self.actor is not None:
            self.actor.stop()
            self.__image_queue.queue.clear()
            self.actor.destroy()
            state = True
        return state
