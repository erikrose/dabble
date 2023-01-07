from .interpreter import run

from sys import argv


def main():
    with open(argv[1], 'r') as file:
        print(run(file.read()))
