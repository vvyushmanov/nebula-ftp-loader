import os

from utils import Product, BuildType, input_validator, error_exit


class Parametrizer:
    def __init__(self, product, build_type, branch, install, delete, args):
        if args:
            self.directory = args.directory
            self.product = args.product
            self.build_type = args.build_type
            self.branch = args.branch
            self.install = args.install
            self.delete = args.no_delete
        else:
            self.product = product
            self.build_type = build_type
            self.branch = branch
            self.install = install
            self.delete = delete
            self.directory = None

    def _set_dir(self):
        try:
            os.chdir(self.directory)
        except FileNotFoundError:
            print(
                f"\nWrong directory input: directory {self.directory} does not exist!"
            )
            error_exit()

    def _set_product(self):
        prompt = (
            f"What do you want to install? (input id or name)\n"
            f" 1) {Product.TS.name}\n"
            f" 2) {Product.TG.name}\n"
            f"Select an option: "
        )
        values = {"1": Product.TS.name, "2": Product.TG.name}
        user_input = input_validator(values, prompt).upper()
        self.product = values.get(user_input, user_input)
        print(f"\nProduct: {self.product}\n")
        return self.product

    def _set_build_type(self):
        prompt = (
            f"Select build type (input id or name)\n"
            f" 1) {BuildType.DEV.name}\n"
            f" 2) {BuildType.RC.name}\n"
            f" 3) {BuildType.RELEASE.name}\n"
            f"Select an option: "
        )
        values = {
            "1": BuildType.DEV.name,
            "2": BuildType.RC.name,
            "3": BuildType.RELEASE.name,
        }
        user_input = input_validator(values, prompt).upper()
        self.build_type = values.get(user_input, user_input)
        print(f"\nBuild type: {self.build_type}\n")
        return self.build_type

    def _set_branch_ts(self, prompt):
        if not self.branch:
            user_input = input(prompt).lower()
            if user_input.startswith("ts-"):
                self.branch = user_input
            elif user_input.isnumeric():
                self.branch = "ts-" + user_input
            elif user_input:
                self.branch = user_input
            else:
                self.branch = "develop"
            print(f"\nBranch: {self.branch}\n")
        elif self.branch.lower().startswith("ts-"):
            self.branch = self.branch.lower()

    def _set_branch_tg(self, prompt):
        if not self.branch:
            self.branch = input(prompt).upper() or ""
            print(f"\nBranch: {self.branch}\n")
        elif self.branch.lower() == "develop":
            self.branch = ""
        else:
            self.branch = self.branch.upper()

    def _set_branch(self):
        prompt = "Enter branch name (leave empty for Develop): "
        param = {
            Product.TS.name: self._set_branch_ts,
            Product.TG.name: self._set_branch_tg,
        }
        if self.build_type == BuildType.DEV.name:
            param[self.product](prompt)
        else:
            self.branch = ""
        return self.branch

    def _check_branch(self):
        if (
            Product.TS.name in self.branch.upper()
            or Product.TG.name in self.branch.upper()
        ):
            self.product = self.branch.upper()[:2]
        self.build_type = BuildType.DEV.name

    def set_parameters(self):
        if self.branch:
            self._check_branch()
        params = {
            "product": self.product or self._set_product(),
            "build_type": self.build_type or self._set_build_type(),
            "branch": self._set_branch(),
            "install": self.install,
            "delete": self.delete,
        }
        if self.directory:
            self._set_dir()
        return params.values()
