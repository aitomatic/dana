def initialize():
    from .dotenv import init as dotenv_init

    dotenv_init()


all = ["initialize"]
