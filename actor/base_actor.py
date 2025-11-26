from log import logger


class Base_Actor:
    def __init__(self, world):
        self._world = world
        self._id = None
        self.actor = None

    def destroy(self):
        logger.error("You should implement this method in your subclass")
        raise NotImplementedError()

    def id(self):
        return self._id

    def exist(self):
        return False if self.actor is None else True

    def item(self):
        return self.actor
