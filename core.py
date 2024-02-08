from downloader import Downloader
from ftp import FTPClient
from installer import Installer, cleanup
from parametrizer import Parametrizer


def check_cancelled(func):
    """Декоратор для проверки, не отменена ли операция перед выполнением метода."""

    def wrapper(self, *args, **kwargs):
        if not self.cancelled:
            return func(self, *args, **kwargs)
        else:
            pass

    return wrapper


class Core:
    def __init__(
        self,
        args=None,
        product=None,
        build_type=None,
        branch=None,
        install=None,
        delete=None,
        gui=False,
        progress_var=None,
        gui_window=None,
        download_speed=None,
        time_remaining=None,
        progressbar=None,
    ):
        self.file = None
        self.latest_build = None
        self.ftp_client = None
        self.cancelled = False
        self.gui_window = gui_window
        self.gui = gui
        self.product = product
        self.build_type = build_type
        self.branch = branch
        self.install = install
        self.delete = delete
        self.progress_var = progress_var
        self.args = args
        self.downloader = None
        self.download_speed = download_speed
        self.time_remaining = time_remaining
        self.progressbar = progressbar

    def execute(self):
        self.parametrize(self)
        self.connect_ftp(self)
        self.get_latest_build(self)
        self.download_file(self)
        self.run_install(self)

    @check_cancelled
    def parametrize(self, *args, **kwargs):
        (
            self.product,
            self.build_type,
            self.branch,
            self.install,
            self.delete,
        ) = Parametrizer(
            self.product,
            self.build_type,
            self.branch,
            self.install,
            self.delete,
            self.args,
        ).set_parameters()

    @check_cancelled
    def connect_ftp(self, *args, **kwargs):
        self.ftp_client = FTPClient(
            self.product, self.build_type, self.branch, self.gui_window
        )
        self.ftp_client.connect()

    @check_cancelled
    def get_latest_build(self, *args, **kwargs):
        self.latest_build = self.ftp_client.get_latest_build()
        if not self.latest_build:
            print(
                "Something went wrong while getting latest build. Please check parameters."
            )

    @check_cancelled
    def download_file(self, *args, **kwargs):
        self.downloader = Downloader(
            self.ftp_client.client,
            self.product,
            self.build_type,
            self.branch,
            self.latest_build,
            self.gui,
            self.progress_var,
            self.download_speed,
            self.time_remaining,
        )
        try:
            self.file = self.downloader.get_file()
            if self.gui:
                self.download_speed.set(0)
        except TimeoutError as e:
            print(f"Download error: {e}")
            self.stop_download()
        except Exception:
            pass

    @check_cancelled
    def run_install(self, *args, **kwargs):
        installer = Installer(
            self.product,
            self.file,
            self.install,
            self.delete,
            self.gui_window,
            self.progressbar,
        )
        try:
            if self.gui:
                self.gui_window.after(0, installer.install_progressbar_on)
            if self.file:
                installer.install_app()
        except Exception as e:
            print(e)
        finally:
            if self.gui:
                self.gui_window.after(0, installer.install_progressbar_off)
                self.progress_var.set(0)

    def stop_download(self):
        self.cancelled = True
        try:
            self.downloader.stop()
            if self.delete:
                cleanup(self.downloader.file_path)
        except Exception:
            pass
        try:
            self.ftp_client.client.abort()
        except Exception:
            pass
        try:
            self.ftp_client.client.close()
        except Exception:
            pass
