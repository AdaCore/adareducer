class ChunkInterface(object):
    """One atomic actionable/undoable operation"""

    def __init__(self):
        pass

    def do(self):
        """Apply the modification"""
        pass

    def undo(self):
        """Undo the modification"""
        pass


class StrategyInterface(object):
    """Interface for reducing strategies"""

    def __init__(self):
        pass

    def run_on_file(self, unit, lines, predicate):
        """Run the strategy on unit, modifying lines.
           Return StrategyStats
        """
        pass
