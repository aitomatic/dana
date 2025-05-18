from .base_function import BaseFunction, BaseFunctionRegistry


class PythonFunction(BaseFunction):
    def __init__(self, func):
        self.func = func

    def call(self, context, *args, **kwargs):
        return self.func(*args, **kwargs)


class PythonRegistry(BaseFunctionRegistry):
    pass  # Add any Python-specific logic if needed
