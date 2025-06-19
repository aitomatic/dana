import unittest

import pytest


@pytest.mark.deep
class TestPipeline(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
