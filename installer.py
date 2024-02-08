import ctypes
import os
import subprocess
import sys
import time

from utils import get_platform, Product, error_exit


def cleanup(file):
    time.sleep(1)
    if os.path.exists(file):
        print("\n" + ("=" * 50))
        print(f"\nCleanup for {file}...\n")
        try:
            os.remove(file)
        except Exception as e:
            print(f"\nError removing file: {e}")
            return
        else:
            print(f"Deleted: {file}")
        dir_cleaner(file)
    else:
        print("All temp files deleted")


def dir_cleaner(filepath):
    dir_name = os.path.dirname(filepath)
    if os.path.isdir(dir_name):
        while not os.listdir(dir_name):
            try:
                os.rmdir(dir_name)
                print(f"Deleted: {dir_name}")
                dir_name = os.path.split(dir_name)[0]
            except Exception as e:
                print(e)
    else:
        print("\nGiven directory doesn't exist")


def get_root_fldr():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    else:
        return os.path.dirname(__file__)


def get_adb():
    system = get_platform()
    adb = {
        "win": f"{get_root_fldr()}\\adb\\adb.exe",
        "linux": f"{get_root_fldr()}/adb/adb-linux",
        "mac": f"{get_root_fldr()}/adb/adb-mac",
    }

    return adb.get(system, None)


def adb_kill_server():
    return f"{get_adb()} kill-server"


class Installer:
    def __init__(self, product, file_path, install, delete, gui, progressbar=None):
        self.product = product
        self.file_path = file_path
        self.install = install
        self.delete = delete
        self.gui = gui
        self.progressbar = progressbar
        self.install_functions = {
            Product.TS.name: {
                True: lambda: self.install_apk(),
                False: lambda: print(
                    f"\nInstallation skipped. Install apk manually:\nadb install {self.file_path}"
                ),
            },
            Product.TG.name: {
                True: lambda: self.install_pc(),
                False: lambda: print(f"\nThe file is located here:\n{self.file_path}"),
            },
        }

    @staticmethod
    def _error_apk(e, file):
        print(f"\nError installing APK: \n{e}")
        print(f"Install apk manually:\nadb install {file}")
        try:
            subprocess.run(
                adb_kill_server(), shell=True, check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            pass
        error_exit()

    def install_progressbar_on(self):
        self.progressbar.config(mode="indeterminate")
        self.progressbar.start()

    def install_progressbar_off(self):
        self.progressbar.config(mode="determinate")
        self.progressbar.stop()

    def install_apk(self):

        command = f"{get_adb()} install {self.file_path}"
        try:
            print("\nInstalling APK...")
            subprocess.run(command, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if "INSTALL_FAILED_VERSION_DOWNGRADE" in str(e.stderr):
                print(
                    "\nFailed to install the APK due to version downgrade.\nRemoving com.t.sa application..."
                )
                subprocess.run(
                    f"{get_adb()} uninstall com.t.sa", shell=True, check=True
                )
                print("Attempting to install the APK again...")
                try:
                    subprocess.run(command, shell=True, check=True)
                except Exception as e:
                    self._error_apk(e, self.file_path)
            else:
                self._error_apk(e.stderr.decode(), self.file_path)

        try:
            subprocess.run(
                adb_kill_server(), shell=True, check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            pass

        # Удаление APK в случае успешной установки
        print("\nInstallation complete")
        if self.delete:
            cleanup(self.file_path)
        if not self.gui:
            input("Press Enter to exit program...")

    def install_pc(self):
        _platform = get_platform()
        if _platform == "linux":
            try:
                os.chmod(self.file_path, 0o755)
            except Exception as e:
                print(f"\nFailed to set permissions: {e}")
                error_exit()

            try:
                print("\nLaunching application...")
                os.system(self.file_path)
            except Exception as e:
                print(f"\nFailed to launch application: {e}")
                error_exit()
        elif _platform == "win":
            # Проверка, запущен ли скрипт с повышенными привилегиями
            if not ctypes.windll.shell32.IsUserAnAdmin():
                # Если скрипт не запущен с правами администратора, перезапускаем его с повышенными привилегиями
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            try:
                print("Installing T.G...")
                process = subprocess.Popen(self.file_path)
            except Exception as e:
                print(f"\nFailed to open installer: {e}")
                error_exit()
            else:
                # Ожидание завершения процесса установки
                process.wait()
                print("Installation successful!")
                # Удаление файла после установки приложения
                if self.delete:
                    print(f"\nDeleting: {self.file_path}")
                    cleanup(self.file_path)

        elif _platform == "mac":
            try:
                print("Mounting the image...")
                subprocess.call(["open", "-W", self.file_path])
            except Exception as e:
                print(f"\nFailed to open installer: {e}")
                error_exit()
            else:
                print("Please drag the app to Applications")
                if self.delete:
                    cleanup(self.file_path)

    def install_app(self):
        if not self.gui and not self.install:
            # Если в GUI не был выбран инсталляция, спросить в консоли
            self.install = input("Install now? (y/n): ").lower() == "y"

        # Вызвать нужную функцию на основе продукта и решения об инсталляции
        self.install_functions[self.product][self.install]()

        # Если инсталляция не требуется и это не GUI, ожидать ввода перед выходом
        if not self.gui and not self.install:
            input("Press enter to exit program...")
