#!./venv/bin/python3

from Theremulator import Theremulator

import threading
import tkinter as tk


def main():
    theremin = Theremulator(webcam_id=0)
    #theremin.synth.debug()


if __name__ == '__main__':
    main()
