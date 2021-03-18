from curses import wrapper

class Window(object):

    def __init__(self):
        pass

    def run(self, engine):
        self.engine = engine
        wrapper(self.main)

    def main(self, stdscr):
        self.scr = stdscr
        self.scr.clear()

        self.engine.run()
        self.scr.refresh()
        
        self.scr.addstr(0,0, self.scr.getkey())

    def print(self, msg):
        self.scr.addstr(0, 0, msg)

GUI = Window()

def print(msg):
    GUI.print(msg)