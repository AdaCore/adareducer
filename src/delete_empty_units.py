import os
from src.types import Buffer
from src.interfaces import StrategyInterface


class DeleteEmptyUnits(StrategyInterface):
    """ Remove blank lines and standalone comments """

    def run_on_file(self, context, file, predicate):
        buf = Buffer(file)

        # for now don't even use LAL, just delete files that look small
        if len(buf.lines) <= 5:
            os.remove(file)

            if predicate():
                return True
            else:
                # if the predicate failed, put back the original file
                buf.save()

        return False
