"""
doc
string
"""
import json


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    return a / b if b else 0


def return_hello():
    return "hello"


def return_bingo():
    return "bingo"


def run():
    print(return_hello())
    (a, b) = (3, 4)
    result1 = add(a, b)
    result2 = subtract(a, b)
    result3 = multiply(a, b)
    result4 = divide(a, b)
    result_dict = {
        "result1": result1,
        "result2": result2,
        "result3": result3,
        "result4": result4,
    }
    print(json.dumps(result_dict))
    print(return_bingo())


if __name__ == "__main__":
    run()
