from .parser import parse

from sys import argv


def main():
    with open(argv[1], 'r') as file:
        print(parse('(' + file.read() + ')'))
