import os.path

from e3.testsuite.driver.classic import TestAbortWithError

from e3.testsuite.driver.diff import DiffTestDriver, OutputRefiner, Substitute


class ToLower(OutputRefiner):
    """Output refiner to switch to lower case."""

    def refine(self, output):
        return output.lower()


class BaseDriver(DiffTestDriver):
    """Base class to provide common test driver helpers."""

    @property
    def baseline(self):
        # Allow a missing test.out or regex_test.out -- treat as empty
        test_out = self.test_dir("test.out")
        regex_test_out = self.test_dir("regex_test.out")
        regex = False
        if os.path.exists(test_out):
            with open(test_out, encoding=self.default_encoding) as f:
                baseline = f.read()
        elif os.path.exists(regex_test_out):
            with open(regex_test_out, encoding=self.default_encoding) as f:
                baseline = f.read()
            regex = True
        else:
            baseline = ""
            test_out = None

        return (test_out, baseline, regex)

    @property
    def output_refiners(self):
        result = super().output_refiners
        if self.test_env.get("fold_casing", False):
            result.append(ToLower())
        if self.test_env.get("canonicalize_backslashes", False):
            result.append(Substitute("\\", "/"))
        return result

    def set_up(self):
        super().set_up()

        if "description" not in self.test_env:
            raise TestAbortWithError('test.yaml: missing "description" field')
