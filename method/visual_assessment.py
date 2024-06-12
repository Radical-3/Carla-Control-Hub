import math
import time
import cv2
from config import Config
from connect import Connect
from factory import Vehicle_Factory, Sensor_Factory
from log import logger
from processor import Processor
from multiprocessing import Process, Pipe
import numpy as np
from utils import generate_series_offset


def vehicle_process(config, vehicle_control_pipe, name="audi.etron"):
    vehicle_control_pipe[0].close()

    connect = Connect(config)
    traffic_manager_port = connect.get_traffic_manager_port()
    vehicle_factory = Vehicle_Factory(connect)
    vehicle = vehicle_factory.spawn_actor(name)
    vehicle_factory.enable_all_vehicle_autopilot(True, traffic_manager_port)
    connect.async_traffic_manager(True)
    vehicle_control_pipe[1].send(vehicle.id())

    while True:
        if vehicle_control_pipe[1].poll():
            state = vehicle_control_pipe[1].recv()
            if state:
                vehicle_factory.enable_all_vehicle_autopilot(False, traffic_manager_port)
                connect.async_traffic_manager(False)
                vehicle_factory.destroy_actor(vehicle)
                vehicle_factory.clear_factory()
                break
        else:
            connect.tick()
    logger.debug("close vehicle process")


def camera_process(config, camera_control_pipe, camera_data_pipe, vehicle_id, offset):
    camera_control_pipe[0].close()
    camera_data_pipe[0].close()

    connect = Connect(config)
    processor = Processor(config, connect)
    sensor_factory = Sensor_Factory(connect)
    vehicle_factory = Vehicle_Factory(connect)
    vehicle = vehicle_factory.production(vehicle_id)
    camera = sensor_factory.spawn_actor("camera.rgb", vehicle, config.image_size, config.fov, offset)
    processor.add_camera(camera)

    max_fps = 1 / config.visual_assessment_data_retrieval_rate
    while True:
        if camera_control_pipe[1].poll():
            state = camera_control_pipe[1].recv()
            if state:
                processor.remove_camera()
                processor.destroy()
                sensor_factory.destroy_actor(camera)
                sensor_factory.clear_factory()
                break
        else:
            try:
                image, semantic_segmentation, labels, position = processor.process()
                camera_data_pipe[1].send(image)
            except BrokenPipeError:
                logger.info("Message sending was interrupted")
        time.sleep(max_fps)
    logger.debug("close camera process")


def visual_assessment():
    config = Config(logger, './config/base.yaml').item()
    logger.set_config(config)
    num = config.visual_assessment_camera_num

    vehicle_control_pipe = Pipe()
    Process(target=vehicle_process, args=(config, vehicle_control_pipe, "audi.etron",)).start()
    vehicle_control_pipe[1].close()
    vehicle_id = vehicle_control_pipe[0].recv()

    camera_control_pipe_p = dict()
    camera_data_pipe_p = dict()
    offsets = generate_series_offset(config)
    for i in range(num):
        camera_control_pipe = Pipe()
        camera_data_pipe = Pipe()
        Process(target=camera_process,
                args=(config, camera_control_pipe, camera_data_pipe, vehicle_id, offsets[i])).start()
        camera_control_pipe_p[i] = camera_control_pipe[0]
        camera_data_pipe_p[i] = camera_data_pipe[0]
        camera_control_pipe[1].close()
        camera_data_pipe[1].close()

    while not all([camera_data_pipe_p[i].poll() for i in range(num)]):
        pass

    row = math.ceil(math.sqrt(num))
    scale = 1 / row
    results = list()

    is_save = config.visual_assessment_save_video
    video_path = config.visual_assessment_video_path
    fps = config.visual_assessment_video_fps
    video = None
    is_first = True

    while True:
        results = [camera_data_pipe_p[i].recv() if camera_data_pipe_p[i].poll() else results[i] for i in range(num)]
        if len(results) % row != 0:
            results.extend([np.ones_like(results[0])] * (row - len(results) % row))
        image = np.vstack([np.hstack(results[i:i + row]) for i in range(0, len(results), row)])
        frame = cv2.cvtColor(cv2.resize(image, (0, 0), fx=scale, fy=scale), cv2.COLOR_BGRA2BGR)

        if is_first and is_save:
            is_first = False
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            video = cv2.VideoWriter(video_path, fourcc, fps, (frame.shape[1], frame.shape[0]))

        if is_save:
            video.write(frame)
        cv2.imshow("Carla", frame)
        if cv2.waitKey(1) == ord('q'):
            video.release()
            cv2.destroyAllWindows()
            break

    [camera_control_pipe_p[i].send(True) for i in range(num)]
    vehicle_control_pipe[0].send(True)