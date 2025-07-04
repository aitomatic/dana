import pytest

from tests.conftest import run_dana_test_file


@pytest.mark.dana
def test_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file in financial_services scenarios."""
    run_dana_test_file(dana_test_file)
