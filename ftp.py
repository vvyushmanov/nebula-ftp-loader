import json
import os
from time import sleep
from enum import Enum
from ftplib import FTP_TLS, error_perm
from tkinter.simpledialog import askstring

from utils import get_platform, Product, BuildType, error_exit, ExitError


class Function(Enum):
    GET_DIR_PATH = "get_dir_path"
    GET_EXTENSION = "get_extension"
    FILTER = "filter"


class FTPClient:
    def __init__(self, product, build_type, branch, gui_window=None):
        self.ftps_pass = None
        self.gui_window = gui_window
        self.client = FTP_TLS()
        self.product = product
        self.build_type = build_type
        self.branch = branch
        self.base_dir = "/Software/"
        self.build_dir = (
            self.build_type
            if self.build_type == BuildType.RC.name
            else self.build_type.lower()
        )
        self.nebula_dir = os.path.join(os.path.expanduser("~"), ".t.nebula")
        if not os.path.exists(self.nebula_dir):
            os.makedirs(self.nebula_dir)
        self.password_file = os.path.join(self.nebula_dir, "ftps_password.json")
        self.passwd = None
        self.passwd_prompt_active = False

    def try_login(self, user, passwd):
        try:
            self.client.login(user=user, passwd=passwd)
        except Exception as e:
            print(f"\nFTP error: {e}")
            if e.args[0] == "530 Login incorrect.":
                i = 3
                while i > 0:
                    self.ftps_pass = self.prompt_for_password()
                    try:
                        self.client.login(user=user, passwd=self.ftps_pass)
                        break
                    except Exception:
                        i -= 1
                        print(f"\nIncorrect password! {i} attempts left")
                        if i == 0:
                            error_exit()

            else:
                error_exit()

    def connect(self):
        ftps_url = os.getenv("FTP_SERVER")
        self.ftps_pass = self.load_password() or self.prompt_for_password()
        # Connecting to FTPS server
        try:
            self.client.connect(ftps_url, timeout=3)
            print("Logging in...")
            self.try_login("u124894", self.ftps_pass)
            self.save_password(self.ftps_pass)
            self.client.prot_p()
        except ExitError:
            pass
        except TimeoutError:
            print("\nConnection to server timed out, check network.")
            print(
                "If there were multiple incorrect password attempts, your IP might be temporary (~1h) banned"
            )
            error_exit()
        except Exception as e:
            print(f"\nError connecting to FTP: {e}")
            error_exit()
        return self

    def prompt_for_password(self):
        if self.gui_window:
            self.passwd_prompt_active = True
            self.gui_window.after(0, self.prompt_for_password_gui)
            while self.passwd_prompt_active:
                sleep(1)
            if not self.passwd:
                print("No FTP password provided!")
                error_exit()
            return self.passwd
        else:
            return input("Enter FTP password: ")

    def prompt_for_password_gui(self):
        passwd = askstring(
            "FTP password",
            "Enter FTP password for the server",
            show="*",
            parent=self.gui_window,
        )
        self.passwd_prompt_active = False
        self.passwd = passwd

    def save_password(self, password):
        with open(self.password_file, "w") as f:
            json.dump({"password": password}, f)

    def load_password(self):
        if os.path.exists(self.password_file):
            with open(self.password_file, "r") as f:
                data = json.load(f)
            return data.get("password")
        else:
            return None

    def get_dir_path_ts(self):
        build_dir = (
            BuildType.RELEASE.name
            if self.build_type == BuildType.RC.name
            else self.build_type
        )
        product_dir = f"mcxmobile/{build_dir}/{self.branch}"
        return f"{self.base_dir}{product_dir}"

    def get_dir_path_tg(self):
        _platform = get_platform()
        product_dir = f"t-x-dc/{self.build_dir}/{_platform}"
        return f"{self.base_dir}{product_dir}"

    def get_extension_ts(self):
        return "-debug.apk" if self.build_type == BuildType.DEV.name else ".apk"

    @staticmethod
    def get_extension_tg():
        _platform = get_platform()
        return {"win": ".exe", "linux": ".AppImage", "mac": ".dmg"}.get(_platform, "")

    def execute(self, function_type):
        function_map = {
            Product.TG.name: {
                Function.GET_DIR_PATH: self.get_dir_path_tg,
                Function.GET_EXTENSION: self.get_extension_tg,
            },
            Product.TS.name: {
                Function.GET_DIR_PATH: self.get_dir_path_ts,
                Function.GET_EXTENSION: self.get_extension_ts,
            },
        }
        if self.product in function_map and function_type in function_map[self.product]:
            return function_map[self.product][function_type]()
        else:
            print("\nInvalid product or function_type value.")

    def filter(self, filename, extension):
        function_map = {
            Product.TG.name: lambda: filename.endswith(extension)
            and (
                self.branch in filename
                if self.branch
                else self.build_dir in filename
                and filename.split(f"-{self.build_dir}")[1][1].isdigit()
            ),
            Product.TS.name: lambda: filename.endswith(extension),
        }
        if self.product in function_map:
            return function_map[self.product]()

    def list_files(self):
        file_dir = self.execute(Function.GET_DIR_PATH)
        try:
            self.client.cwd(file_dir)
        except error_perm:
            print(f"\nDirectory {file_dir} not found on the server!")
            error_exit()
        except Exception as e:
            print(f"\nError: {e}")
            error_exit()

        try:
            file_list = {}
            for name, attr in self.client.mlsd(facts=["modify"]):
                file_list[name] = attr["modify"]
            return file_list, file_dir
        except Exception as e:
            print(f"\nError listing FTP directory: {e}")
            error_exit()

    def get_latest_build(self):
        file_list, file_dir = self.list_files()
        print(f"\nScanning FTP folder {file_dir}...")
        extension = self.execute(Function.GET_EXTENSION)
        builds_list = {
            filename: modified_at
            for filename, modified_at in file_list.items()
            if self.filter(filename, extension)
        }
        if builds_list:
            latest_build = max(builds_list, key=builds_list.get)
            print(f"\nLatest build: {latest_build}")
            return latest_build
        else:
            print(f"\nNo matching builds found in {file_dir}")
            error_exit()
