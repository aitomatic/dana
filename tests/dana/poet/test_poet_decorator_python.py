from opendxa.dana.poet.decorator import poet
from opendxa.dana.sandbox.interpreter import Interpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestInterpreter(Interpreter):
    """Simple test interpreter that does nothing."""

    pass


def create_test_context() -> SandboxContext:
    """Create a test context with an interpreter."""
    context = SandboxContext()
    context._interpreter = TestInterpreter()
    return context


def test_poet_decorator_returns_function():
    @poet(domain="test_domain", retries=2, timeout=10)
    def my_func(x):
        return x * 2

    assert callable(my_func)
    assert not hasattr(my_func, "metadata")  # Should not be a POETDecorator instance
    assert hasattr(my_func, "_poet_metadata")
    meta = my_func._poet_metadata
    assert meta["domains"] == {"test_domain"}
    assert meta["retries"] == 2
    assert meta["timeout"] == 10
    assert meta["namespace"] == "local"
    assert meta["overwrite"] is False
    assert meta["enable_training"] is False
    assert my_func(3, context=create_test_context()) == 6


def test_poet_decorator_retry_logic():
    calls = {"count": 0}

    @poet(domain="test_domain", retries=3)
    def sometimes_fails(x):
        calls["count"] += 1
        if calls["count"] < 2:
            raise ValueError("fail once")
        return x + 1

    assert sometimes_fails(5, context=create_test_context()) == 6
    assert calls["count"] == 2  # Should retry once


def test_poet_decorator_metadata_fields():
    @poet(domain="my_domain", retries=4, timeout=7, namespace="custom", overwrite=True, enable_training=True)
    def f(x):
        return x

    meta = f._poet_metadata
    assert meta["domains"] == {"my_domain"}
    assert meta["retries"] == 4
    assert meta["timeout"] == 7
    assert meta["namespace"] == "custom"
    assert meta["overwrite"] is True
    assert meta["enable_training"] is True


def test_poet_decorator_preserves_doc_and_name():
    @poet(domain="test_domain")
    def f(x):
        """This is a test docstring."""
        return x

    assert f.__name__ == "f"
    assert f.__doc__ == "This is a test docstring."
