# Utility types

from distutils.log import debug


DEBUG = False

debug_counter = 1

class SLOC(object):
    def __init__(self, line, column):
        self.line = line
        self.column = column

    def __str__(self):
        return f"{self.line}:{self.column}"


class SLOC_Range(object):
    def __init__(self, sloc_start, sloc_end):
        self.start = sloc_start
        self.end = sloc_end

    def __str__(self):
        return f"{self.start}-{self.end}"


class Buffer(object):
    """Represents the contents of a file"""

    def __init__(self, filename):
        """Reads the buffer from disk"""
        self.filename = filename
        self.lines = []
        # a list containing None plus the text of the file

        self.load()

    def load(self):
        """ Return the contents of file as an array of lines, with
            an extra empty one at the top so that line numbers correspond
            to indexes
        """
        with open(self.filename, "rb") as f:
            try:
                self.lines = [None] + f.read().decode("latin-1").splitlines()
            except UnicodeDecodeError:
                print(f"{self.filename}: could not decode latin-1, trying with unicode")
                try:
                    self.lines = [None] + f.read().decode().splitlines()
                except UnicodeDecodeError:
                    print("DECODE FAILED, skipping contents")
                    self.lines = [None] + [""]

    def save(self, to_file=None):
        """ Write buffer to file from its line array, popping the one at first"""
        global debug_counter
        tgt = to_file if to_file is not None else self.filename
        with open(tgt, "w") as f:
            f.write("\n".join(self.lines[1:]) + "\n")

        if DEBUG:
            tgt_dbg = tgt + "." + str(debug_counter)
            with open(tgt_dbg, "w") as f:
                debug_counter += 1
                print(f"saving {tgt_dbg}")
                f.write("\n".join(self.lines[1:]) + "\n")


    def replace(self, sloc_range, new_lines):
        """See below"""
        return replace(self.lines, sloc_range, new_lines)

    def strip_tabs(self):
        newlines = [None]
        for l in self.lines[1:]:
            newlines.append(l.replace("\t", ""))
        self.lines = newlines

    def count_chars(self):
        return count_chars(self.lines)


class Checkpoint(object):
    """Create a checkpoint on a number of buffers

    This is meant to use as a context manager:
         with Checkpoint(buffers) as c:
             # do some operations that change the buffer
             # if the operations are successful, call this:
             c.accept()
             # if not, simply exit. Or call c.discard(). This
             # will revert the changes
    """
    def __init__(self, buffers):
        """buffers is a set of buffers"""
        self.buffers = buffers
        # Make a copy of the buffer lines
        self.saved_lines = {buffer : list(buffer.lines) for buffer in self.buffers}

        # Whether the user has accepted or discarded the changes
        # manually, through a call to accept or discard
        self.user_acted = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self.user_acted:
            self.discard()
        if exc_type is not None:
            raise
        return False

    def accept(self):
        self.user_acted = True

    def discard(self):
        for buf in self.buffers:
            buf.lines = self.saved_lines[buf]
        self.user_acted = True


def replace(lines, sloc_range, new_lines):
    """ Replace text at the given range with the new lines.

        return a tuple:
         (the sloc range for the new data,
          data that was replaced as lines)

       to ease undoing the replace"""

    # cut
    text = (
        lines[sloc_range.start.line][0 : sloc_range.start.column - 1]
        + lines[sloc_range.end.line][sloc_range.end.column - 1 :]
    )
    if sloc_range.end.line == sloc_range.start.line:
        result = [
            lines[sloc_range.start.line][
                sloc_range.start.column - 1 : sloc_range.end.column - 1
            ]
        ]
    else:
        result = [lines[sloc_range.start.line][sloc_range.start.column - 1 :]]
        for j in range(sloc_range.start.line + 1, sloc_range.end.line):
            result.append(lines[j])
        result.append(lines[sloc_range.end.line][0 : sloc_range.end.column - 1])
        for j in range(sloc_range.end.line - sloc_range.start.line):
            lines.pop(sloc_range.start.line)

    lines[sloc_range.start.line] = text

    # insert new text
    if len(new_lines) == 0:
        pass
    elif len(new_lines) == 1:
        lines[sloc_range.start.line] = (
            lines[sloc_range.start.line][0 : sloc_range.start.column - 1]
            + new_lines[0]
            + lines[sloc_range.start.line][sloc_range.start.column - 1 :]
        )
    else:
        end_bit = lines[sloc_range.start.line][sloc_range.start.column - 1 :]
        lines[sloc_range.start.line] = (
            lines[sloc_range.start.line][0 : sloc_range.start.column - 1] + new_lines[0]
        )
        for j in range(1, len(new_lines) - 1):
            lines.insert(sloc_range.start.line + j, new_lines[j])
        lines.insert(
            sloc_range.start.line + len(new_lines) - 1, new_lines[-1] + end_bit
        )

    if len(new_lines) == 1:
        end_sloc = SLOC(
            sloc_range.start.line, sloc_range.start.column + len(new_lines[0])
        )
    else:
        end_sloc = SLOC(
            sloc_range.start.line + len(new_lines) - 1, len(new_lines[-1]) + 1
        )

    return (SLOC_Range(sloc_range.start, end_sloc), result)


def count_chars(lines):
    """ Count the characters in lines """
    count = 0
    for l in lines[1:]:
        count += len(l) + 1  # The + 1 is the line terminator
    return count


def infer_or_equal(a, b):
    """compare two sloc ranges"""
    if a.line < b.line:
        return True
    elif a.line > b.line:
        return False
    else:
        return a.column <= b.column
