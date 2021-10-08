from enum import Enum, auto

class States(Enum):
    S_STARTUP = auto()
    S_AVAILABLE = auto()
    S_NOTAVAILABLE = auto()
    S_PLUGINCABLE = auto()
    S_AUTHORIZING = auto()
    S_CONNECTING = auto()
    S_DISCONNECT = auto()
    S_CHARGING = auto()
    S_BATTERYFULL = auto()


class StateHandler:
    def __init__(self):
        self.__state = States.S_STARTUP

    def set_state(self, state):
        self.__state = state

    def get_state(self):
        return self.__state