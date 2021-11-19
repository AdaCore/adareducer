from adareducer.types import Buffer
from adareducer.interfaces import StrategyInterface


class RemoveTrivias(StrategyInterface):
    """ Remove blank lines and standalone comments """

    def run_on_file(self, file, predicate):
        buf = Buffer(file)
        orig = list(buf.lines)
        last_was_null = False

        # strip manually
        new = [None]
        for line in buf.lines[1:]:
            stripped = line.strip()
            if stripped == "" or stripped.startswith("--"):
                pass

            elif stripped == "null;":
                # Strip successive "null;" statements
                if not last_was_null:
                    new.append(line)
                last_was_null = True
            else:
                last_was_null = False
                new.append(line)

        buf.lines = new
        buf.save()

        if not predicate():
            # if the predicate failed, put back the orig lines
            buf.lines = orig
            buf.save()
