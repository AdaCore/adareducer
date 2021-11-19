# In some environment (e.g. Windows), this module is not disfunctional
try:
    from curses import wrapper
except ModuleNotFoundError:
    wrapper = None


debug = False
debug = True


class Window(object):
    def __init__(self):
        self.characters_removed = 0

    def run(self, engine):
        self.engine = engine
        if debug or wrapper is None:
            self.engine.run()
        else:
            wrapper(self.main)

    def add_chars_removed(self, count):
        """Tell the gui that count characters have been removed"""
        self.characters_removed += count
        self.log(f"Total characters removed: {self.characters_removed}")

    def main(self, stdscr):
        self.scr = stdscr
        self.scr.clear()

        self.engine.run()
        self.scr.refresh()
        self.scr.getkey()

    def log(self, msg):
        if debug:
            print(msg)
        else:
            self.scr.addstr(0, 0, str(msg))


GUI = Window()


def log(msg):
    GUI.log(msg)
