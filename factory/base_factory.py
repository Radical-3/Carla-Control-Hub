from log import logger


class Base_Factory:
    def __init__(self, connect=None):
        self._client = connect.client()
        self._world = connect.world()
        self._blueprint_library = self._world.get_blueprint_library()
        self._actor_id_list = list()

    def spawn_actor(self):
        logger.error("You should implement this method in your subclass")
        raise NotImplementedError()

    def production(self, actor_id):
        logger.error("You should implement this method in your subclass")
        raise NotImplementedError()

    def destroy_actor(self, actor_id):
        logger.error("You should implement this method in your subclass")
        raise NotImplementedError()

    def clear_factory(self):
        logger.error("You should implement this method in your subclass")
        raise NotImplementedError()
