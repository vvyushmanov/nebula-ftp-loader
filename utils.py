import argparse
import ctypes
import platform
import sys
import threading
from enum import Enum


def create_args_parser():
    parser = argparse.ArgumentParser(
        description="A super fancy script to download *** client application from the FTP server."
    )
    parser.add_argument(
        "--no_gui", action="store_true", help="Start application in console mode"
    )
    parser.add_argument(
        "-p",
        "--product",
        choices=[Product.TS.name, Product.TG.name],
        help="Choose between T.S " "and T.G",
    )
    parser.add_argument(
        "-t",
        "--build_type",
        choices=[BuildType.DEV.name, BuildType.RC.name, BuildType.RELEASE.name],
        help="Build type",
    )
    parser.add_argument(
        "-b",
        "--branch",
        type=str,
        help='Branch name, e.g. "TS-666". If provided, sets product and build type '
        'automatically.\nSet to "develop" for main develop build.',
    )
    parser.add_argument(
        "-y",
        "--install",
        action="store_true",
        help="Install/launch the app once downloaded",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Set the working directory for the script (root folder for download).",
    )
    parser.add_argument(
        "--no_delete",
        action="store_false",
        help="Don't delete the downloaded file and directory after successful installation",
    )

    return parser


class ExitError(Exception):
    pass


class DownloadInterrupted(Exception):
    pass


def error_exit(exception=None):
    print("\n")
    if exception:
        print(exception)
    exit_text = "An error occurred (see above)"
    if threading.current_thread().name == "MainThread":
        print(exit_text)
        input("Press Enter to exit program...")
        sys.exit(1)
    else:
        raise ExitError(exit_text)


def hide_console_win():
    kernel32 = ctypes.WinDLL("kernel32")
    user32 = ctypes.WinDLL("user32")
    SW_HIDE = 0
    hWnd = kernel32.GetConsoleWindow()
    user32.ShowWindow(hWnd, SW_HIDE)


def get_platform():
    system = platform.system()
    if system == "Windows":
        return "win"
    elif system == "Linux":
        return "linux"
    elif system == "Darwin":
        return "mac"
    else:
        print("Can't determine OS")
        error_exit()


def input_validator(valid_values, prompt):
    user_input = input(prompt)
    attempts = 1

    if type(valid_values) == dict:
        values = []
        for key, value in valid_values.items():
            values.append(key)
            values.append(value)
        valid_values = values

    while user_input.lower() not in [value.lower() for value in valid_values]:
        print(f"\nIncorrect value, please try again\n")
        attempts += 1

        if attempts > 3:
            print("Too many failed attempts")
            error_exit()

        user_input = input(prompt)

    return user_input


class Product(Enum):
    TG = "TG"
    TS = "TS"


class BuildType(Enum):
    RELEASE = "RELEASE"
    DEV = "DEV"
    RC = "RC"
