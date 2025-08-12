# Python utility functions for testing Dana imports
def greet(name):
    return f"Hello, {name}!"


def calculate_sum(numbers):
    return sum(numbers)


class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_info(self):
        return f"{self.name} is {self.age} years old"


# A constant to test
MAGIC_NUMBER = 42
