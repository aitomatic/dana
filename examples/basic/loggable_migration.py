"""Demonstrates how to migrate existing classes to use the Loggable base class."""

import logging
from dxa.common.utils.logging import Loggable, DXA_LOGGER

# Configure root logger to show all logs
logging.basicConfig(level=logging.INFO)

# Configure global logging level with console output
DXA_LOGGER.configure(level=logging.INFO, console=True)

print("Migration example started")
print("\n=== BEFORE MIGRATION ===")

class BeforeExecutor:
    """Example of a class before migration to Loggable."""
    
    def __init__(self, depth=0):
        self.depth = depth
        self.layer = "executor"
        # Manual logger setup
        self.logger = logging.getLogger("dxa.execution.%s" % self.layer)
        self.logger.setLevel(logging.INFO)
        # Add a handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - [%(name)s] %(levelname)s - %(message)s", 
                "%H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.info("Executor initialized with depth: %d", depth)
    
    def execute(self, task):
        """Execute a task."""
        self.logger.debug("Executing task: %s", task)
        result = f"Executed: {task}"
        self.logger.info("Task execution complete")
        return result


class BeforePlanExecutor(BeforeExecutor):
    """Example of a subclass before migration."""
    
    def __init__(self, strategy="default"):
        super().__init__(depth=1)
        self.strategy = strategy
        self.layer = "planning"
        # Need to reinitialize logger with new layer
        self.logger = logging.getLogger("dxa.execution.%s" % self.layer)
        # Add a handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - [%(name)s] %(levelname)s - %(message)s", 
                "%H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.info("Plan executor initialized with strategy: %s", strategy)
    
    def plan(self, objective):
        """Plan execution for an objective."""
        self.logger.debug("Planning for objective: %s", objective)
        result = f"Plan for: {objective}"
        self.logger.info("Planning complete")
        return result


# Demonstrate the before classes
before_executor = BeforeExecutor()
before_executor.execute("simple task")

before_plan = BeforePlanExecutor()
before_plan.plan("achieve goal")


print("\n=== AFTER MIGRATION ===")

class AfterExecutor(Loggable):
    """Example of a class after migration to Loggable."""
    
    def __init__(self, depth=0):
        self.depth = depth
        self.layer = "executor"
        # Just call super().__init__() - that's it!
        super().__init__()
        self.logger.info("Executor initialized with depth: %d", depth)
    
    def execute(self, task):
        """Execute a task."""
        self.logger.debug("Executing task: %s", task)
        result = f"Executed: {task}"
        self.logger.info("Task execution complete")
        return result


class AfterPlanExecutor(AfterExecutor):
    """Example of a subclass after migration."""
    
    def __init__(self, strategy="default"):
        # Set layer before calling parent __init__
        self.layer = "planning"
        super().__init__(depth=1)
        self.strategy = strategy
        self.logger.info("Plan executor initialized with strategy: %s", strategy)
    
    def plan(self, objective):
        """Plan execution for an objective."""
        self.logger.debug("Planning for objective: %s", objective)
        result = f"Plan for: {objective}"
        self.logger.info("Planning complete")
        return result


# Demonstrate the after classes
after_executor = AfterExecutor()
after_executor.execute("simple task")

after_plan = AfterPlanExecutor()
after_plan.plan("achieve goal")


print("\n=== MIGRATION WITH MULTIPLE INHERITANCE ===")

class Resource:
    """Example of another base class."""
    
    def __init__(self, name):
        self.name = name
        print(f"Resource initialized with name: {name}")


class BeforeResourceExecutor(Resource, BeforeExecutor):
    """Example of multiple inheritance before migration."""
    
    def __init__(self, name, depth=0):
        Resource.__init__(self, name)
        BeforeExecutor.__init__(self, depth)
        self.logger.info("Resource executor initialized")


class AfterResourceExecutor(Resource, AfterExecutor):
    """Example of multiple inheritance after migration."""
    
    def __init__(self, name, depth=0):
        Resource.__init__(self, name)
        # With Loggable, the initialization is much simpler
        AfterExecutor.__init__(self, depth)
        # Logger is already set up correctly
        self.logger.info("Resource executor initialized")


# Demonstrate multiple inheritance
before_resource = BeforeResourceExecutor("before-resource")
after_resource = AfterResourceExecutor("after-resource") 