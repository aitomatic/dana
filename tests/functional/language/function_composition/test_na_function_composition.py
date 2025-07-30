import pytest

from tests.conftest import run_dana_test_file


@pytest.mark.dana
def test_function_composition(dana_test_file):
    """Universal test that runs any Dana (.na) test file in function_composition."""
    run_dana_test_file(dana_test_file)
