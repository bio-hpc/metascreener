#!/usr/bin/env python2
# -*- coding: utf-8 -*-


class Debug(object):

    def __init__(self, mode_debug):
        self.mode_debug = mode_debug

    def show(self, text, color):
        if int(self.mode_debug) > 0:
            t = text.split("\n")
            for i in t:
                print(BColors.WARNING + "DEBUG: "+color+i + BColors.ENDC)


class BColors(object):
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def __init__(self):
        pass
