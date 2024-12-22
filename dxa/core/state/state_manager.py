class StateManager:
    def __init__(self):
        self._state = {}
        
    def get_state(self) -> Dict[str, Any]:
        return self._state
        
    def update_state(self, key: str, value: Any) -> None:
        self._state[key] = value 