# Utility types


class SLOC(object):
    def __init__(self, line, column):
        self.line = line
        self.column = column


class SLOC_Range(object):
    def __init__(self, sloc_start, sloc_end):
        self.start = sloc_start
        self.end = sloc_end


def replace(lines, sloc_range, new_lines):
    """ Replace text at the given range with the new lines.

        return a tuple:
         (the sloc range for the new data,
          data that was replaced as lines)

       to ease undoing the replace"""

    # Deal with the first line
    first_bit = lines[sloc_range.start.line][0 : sloc_range.start.column - 1]
    last_bit = lines[sloc_range.end.line][sloc_range.end.column - 1 :]
    if sloc_range.start.line == sloc_range.end.line:
        result = [
            lines[sloc_range.start.line][
                sloc_range.start.column - 1 : sloc_range.end.column - 1
            ]
        ]
    else:
        result = [lines[sloc_range.start.line][sloc_range.start.column - 1 :]]
    lines[sloc_range.start.line] = first_bit + new_lines[0]

    # Middle bit
    # Pop all the existing lines into result
    for _ in range(1, sloc_range.end.line - sloc_range.start.line - 1):
        result.append(lines.pop(sloc_range.start.line + 1))

    # Insert all the lines
    for r in range(1, len(new_lines) - 1):
        lines.insert(sloc_range.start.line + r - 1, new_lines[r])

    # End bit

    lastline = sloc_range.start.line + len(new_lines) - 1

    if sloc_range.start.line == sloc_range.end.line:
        lines[sloc_range.start.line] = lines[sloc_range.start.line] + last_bit
    else:
        result.append(lines[lastline][0 : sloc_range.end.column - 1])
        lines[lastline] = new_lines[-1] + last_bit

    if len(new_lines) == 1:
        end_sloc = SLOC(
            sloc_range.start.line, sloc_range.start.column + len(new_lines[0])
        )
    else:
        end_sloc = SLOC(
            sloc_range.start.line + len(new_lines) - 1, len(new_lines[-1]) + 1
        )

    return (SLOC_Range(sloc_range.start, end_sloc), result)


def read_file(file):
    """ Return the contents of file as an array of lines, with
        an extra empty one at the top so that line numbers correspond
        to indexes
    """
    with open(file, "rb") as f:
        return [None] + f.read().decode().splitlines()


def write_file(file, lines):
    """ Write buffer to file from its line array, popping the one at first"""
    with open(file, "w") as f:
        f.write("\n".join(lines[1:]) + "\n")
