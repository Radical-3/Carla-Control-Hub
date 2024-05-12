from log import logger
from .base_actor import Base_Actor


class Vehicle(Base_Actor):
    def __init__(self, world, blueprint=None, spawn_point=None, actor_id=None):
        super().__init__(world)

        if actor_id is not None:
            self._actor = self._world.get_actor(actor_id)
        else:
            self._actor = self._world.try_spawn_actor(blueprint, spawn_point)

        if self._actor is not None:
            self._id = self._actor.id

    def set_autopilot(self, state, traffic_manager_port=8000):
        if self._actor is not None:
            self._actor.set_autopilot(state, traffic_manager_port)
            logger.debug(f"Set autopilot {state} successfully")
        else:
            logger.error(f"Set autopilot {state} failed")

    def destroy(self):
        state = False
        if self._actor is not None:
            self._actor.set_autopilot(False)
            self._actor.destroy()
            state = True
        return state
