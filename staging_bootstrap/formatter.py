"""
Copyright (C) 2017 DataCentred Ltd - All Rights Reserved
"""

import sys


def info(message):
    """Echos a message to stdout with infomational priority"""

    sys.stdout.write("[1;32m>>> {}[0m".format(message))
    if message[-1] != "\n":
        sys.stdout.write("\n")


def detail(message):
    """Echos a message to stdout with detail priority"""

    sys.stdout.write("    [1m{}[0m".format(message))
    if message[-1] != "\n":
        sys.stdout.write("\n")


# vi: ts=4 et:
