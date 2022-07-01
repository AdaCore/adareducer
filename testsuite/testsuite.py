#! /usr/bin/env python

"""
Usage::

    testsuite.py [OPTIONS]

Run the adareducer testsuite. This requires e3-testsuite.
"""

import os
import sys

import e3.testsuite

from drivers.shell_script import ShellScriptDriver


class AdaReducerTestsuite(e3.testsuite.Testsuite):
    tests_subdir = "tests"
    test_driver_map = {"shell_script": ShellScriptDriver}
    default_driver = "shell_script"

    def add_options(self, parser):
        parser.add_argument(
            "--no-auto-path",
            dest="auto_path",
            action="store_false",
            help="Do not automatically make adareducer available, i.e. assume"
            " it is already available in the environment."
        )

    def set_up(self) -> None:
        super().set_up()

        if self.env.options.auto_path:
            # Set PYTHONPATH to find adareducer
            root_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )
            os.environ["PYTHONPATH"] = "{}:{}".format(
                root_dir,
                os.environ.get("PYTHONPATH", ""),
            )

            os.environ["ADAREDUCER"] = f"{root_dir}/adareducer"

        else:
            os.environ["ADAREDUCER"] = "adareducer"

if __name__ == "__main__":
    sys.exit(AdaReducerTestsuite(os.path.dirname(__file__)).testsuite_main())
