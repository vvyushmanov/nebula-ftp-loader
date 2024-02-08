from core import Core
from gui import FTPLoaderGUI
from utils import create_args_parser, get_platform, hide_console_win


def main():
    args = create_args_parser().parse_args()
    if args.no_gui:
        Core(args=args).execute()
    else:
        if get_platform() == "win":
            hide_console_win()
        FTPLoaderGUI().run()


if __name__ == "__main__":
    main()
