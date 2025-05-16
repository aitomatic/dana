from opendxa.dana.sandbox.sandbox_context import SandboxContext

from .base_function import BaseFunction, BaseFunctionRegistry


class DanaFunction(BaseFunction):
    def __init__(self, ast, params, closure_context=None):
        self.ast = ast
        self.params = params
        self.closure_context = closure_context

    def call(self, context, *args, **kwargs):
        # 1. Create a new SandboxContext with closure_context as parent
        new_context = SandboxContext(parent=self.closure_context or context)
        # 2. Bind parameters to args/kwargs in new_context
        for name, value in zip(self.params, args):
            new_context.set(name, value)
        for k, v in kwargs.items():
            new_context.set(k, v)
        # 3. Execute the function body AST in new_context
        from opendxa.dana.sandbox.interpreter.interpreter import Interpreter

        interpreter = Interpreter(new_context)
        return interpreter.execute_program(self.ast)


class DanaRegistry(BaseFunctionRegistry):
    pass
