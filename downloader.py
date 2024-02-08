import datetime
import os
import time

from utils import Product, error_exit, DownloadInterrupted


class Downloader:
    def __init__(
        self,
        ftp_client,
        product,
        build_type,
        branch,
        filename,
        gui,
        progress_var,
        download_speed,
        time_remaining,
    ):
        self.elapsed_time = None
        self.time_remaining = time_remaining
        self.download_speed = download_speed
        self.ftp_client = ftp_client
        self.product = product
        self.build_type = build_type
        self.branch = branch
        self.filename = filename
        self.gui = gui
        self.file_size = 0
        self.nebula_dir = os.path.join(os.path.expanduser("~"), ".t.nebula")
        if not os.path.exists(self.nebula_dir):
            os.makedirs(self.nebula_dir)
        self._dir = None
        self.file_path = None
        self.progress = 0
        self.progress_var = progress_var
        self.stop_requested = False
        self.start_time = None

    def stop(self):
        self.stop_requested = True
        self.progress_var.set(0)

    def _set_file_params(self):
        self.branch = (
            ""
            if self.product == Product.TS.name and self.branch == "develop"
            else self.branch
        )
        self._dir = os.path.join(
            self.nebula_dir, self.product, self.build_type, self.branch
        )
        try:
            self.file_path = os.path.join(self._dir, self.filename)
        except TypeError:
            print("\nIncorrect path to file")
            error_exit()
        self.ftp_client.voidcmd("TYPE I")
        self.file_size = self.ftp_client.size(self.filename)

    def calculate_download_speed(self):
        self.elapsed_time = time.time() - self.start_time
        if self.elapsed_time > 0:
            self.download_speed.set(
                (self.progress / self.elapsed_time) * 8 / (1024 * 1024)
            )

    def calculate_remaining_time(self):
        self.time_remaining.set(
            int(
                (self.file_size / (self.progress / self.elapsed_time))
                - self.elapsed_time
            )
        )

    def _loader(self, data, file):
        if not file.closed:
            file.write(data)
        if self.stop_requested:
            file.close()
            try:
                self.ftp_client.quit()
            except AttributeError:
                pass
            raise DownloadInterrupted("Download interrupted")
        self.progress += len(data)

        if self.gui:
            self.calculate_download_speed()
            self.calculate_remaining_time()

        progress = self.progress / self.file_size
        if self.gui:
            self.progress_var.set(progress * 100)
        else:
            bar_length = 50
            done = int(progress * bar_length)
            progress_bar = "\u2593" * done + "\u2591" * (bar_length - done)
            print(f"\r{progress_bar} {int(progress * 100)}%", end="", flush=True)

    def _download_file(self):
        print("\nStarting download...")
        os.makedirs(self._dir, exist_ok=True)
        with open(self.file_path, "wb") as file:
            print(f"\nDownloading {self.filename} to {self._dir}")
            self.start_time = time.time()
            try:
                self.ftp_client.retrbinary(
                    f"RETR {self.filename}", lambda data: self._loader(data, file)
                )
            except DownloadInterrupted:
                error_exit()
            except TimeoutError:
                if not self.stop_requested:
                    raise TimeoutError("Connection timed out")
                else:
                    error_exit()
            except Exception as e:
                if not self.stop_requested:
                    error_exit(e)
                else:
                    error_exit()
        if not self.gui:
            print(f"\r{' ' * 55}\r")
        print(f"\nFile downloaded to {self.file_path}")

    def get_file(self):
        self._set_file_params()
        if (
            os.path.isfile(self.file_path)
            and os.stat(self.file_path).st_size == self.file_size
        ):
            print(f"\nFile {self.filename} already downloaded to {self._dir}")
        else:
            self._download_file()

        try:
            self.ftp_client.quit()
        except Exception as e:
            print(f"\nError closing FTP connection: {e}")

        return self.file_path
