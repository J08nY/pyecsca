#!/usr/bin/env python3
from sys import stdout

if __name__ == "__main__":

    while True:
        try:
            line = input()
        except EOFError:
            break
        char = line[0]
        content = line[1:]
        if char == "d":
            for c in "r01020304":
                stdout.write(c)
            stdout.write("\n")
            for c in "z00":
                stdout.write(c)
            stdout.write("\n")
        elif char == "x":
            break
