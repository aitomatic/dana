def pytest_addoption(parser):
    parser.addoption("--ux-review", action="store_true", help="Review UX outputs instead of asserting")
