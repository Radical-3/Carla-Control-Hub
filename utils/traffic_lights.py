def set_traffic_light_to_wait_seconds(world, red_time, yellow_time):
    # 获取所有的 traffic lights（交通灯）
    traffic_lights = world.get_actors().filter('traffic.traffic_light')

    for traffic_light in traffic_lights:
        # 设置红灯时间
        traffic_light.set_red_time(red_time)
        # 设置黄灯时间
        traffic_light.set_yellow_time(yellow_time)

        # 计算绿灯时间：绿灯时间 = 总周期时间 - 红灯时间 - 黄灯时间
        total_cycle_time = traffic_light.get_green_time() + traffic_light.get_red_time() + traffic_light.get_yellow_time()
        green_time = total_cycle_time - red_time - yellow_time

        # 设置绿灯时间
        traffic_light.set_green_time(green_time)