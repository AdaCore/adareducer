from src.types import SLOC, SLOC_Range, replace
from src.interfaces import ChunkInterface
from src.dichotomy import dichotomize

lines = [None, "hello of fun", "beautiful", "world"]


def test_replace():
    r = SLOC_Range(SLOC(1, 6), SLOC(1, 6))
    new_range, old_text = replace(lines, r, [" world"])
    print(f"old text= #{old_text}#")
    print("\n".join(lines[1:]))
    replace(lines, new_range, old_text)
    print("\n".join(lines[1:]))

    print("")

    r = SLOC_Range(SLOC(1, 6), SLOC(2, 7))
    new_range, old_text = replace(lines, r, ["", "wonder"])
    print("\n".join(lines[1:]))

    replace(lines, new_range, old_text)
    print("\n".join(lines[1:]))


class DividerByTwoChunk(ChunkInterface):
    def __init__(self, l, index):
        self.l = l
        self.index = index

    def do(self):
        self.l[self.index] = self.l[self.index] / 2

    def undo(self):
        self.l[self.index] = int(self.l[self.index] * 2)


def test_dichotomy():
    l = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    chunks = [DividerByTwoChunk(l, x) for x in range(0, len(l))]
    res = dichotomize(chunks, lambda: all([int(x) == x for x in l]))
    print(l)
    print("items not dividable by 2:", [l[x.index] for x in res])


# test_dichotomy()
test_replace()
