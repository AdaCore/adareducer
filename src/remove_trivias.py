from src.types import Buffer
from src.interfaces import StrategyInterface


class RemoveTrivias(StrategyInterface):
    """ Remove blank lines and standalone comments """

    def run_on_file(self, file, predicate):
        buf = Buffer(file)
        orig = list(buf.lines)

        # strip manually
        new = [None]
        for line in buf.lines[1:]:
            stripped = line.strip()
            if stripped == "" or stripped.startswith("--"):
                pass
            else:
                new.append(line)

        buf.lines = new
        buf.save()

        if not predicate():
            # if the predicate failed, put back the orig lines
            buf.lines = orig
            buf.save()
