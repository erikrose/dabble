from sys import argv

from .interpreter import run


def main():
    with open(argv[1], 'r') as file:
        print(run(file.read()))
