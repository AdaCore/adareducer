from src.types import SLOC, SLOC_Range, replace
from src.interfaces import ChunkInterface
from src.dichotomy import dichotomize

lines = [None, "hello of fun", "beautiful", "world"]
orig_lines = list(lines)
orig_text = """   function Read222222 (Word : String) return Value is
      Int_Val  : Integer;
      Real_Val : Float;
      Kind     : Input.Number_Kind;

   begin
      Input.Read_Number (Word, Int_Val, Real_Val, Kind);

      if Kind /= Int_Number then
         raise Except.User_Error;
      end if;

      return new Value_Info'(E => Int_Val);
      --  Allocate a new Value_Info (which is a record with one field)
      --  on the heap and initialize its only field "E" to be "Int_Val".
      --  NOTE: the ' in Value_Info'(...) must be there.
   end Read222222;"""


def test_replace():
    r = SLOC_Range(SLOC(1, 6), SLOC(1, 6))
    new_range, old_text = replace(lines, r, [" world"])
    assert old_text == [""]
    assert lines, [None, "hello world of fun", "beautiful", "world"]
    replace(lines, new_range, old_text)
    assert lines, orig_lines

    r = SLOC_Range(SLOC(1, 6), SLOC(2, 7))
    new_range, old_text = replace(lines, r, ["", "wonder"])
    assert str(new_range) == "1:6-2:7"
    replace(lines, new_range, old_text)
    assert lines, orig_lines


def test_replace_fun():
    lines = [None] + orig_text.split("\n")
    orig_lines = list(lines)

    r = SLOC_Range(SLOC(7, 7), SLOC(11, 14))
    new_range, old_text = replace(lines, r, ["null;", "npll;"])
    new_range, old_text = replace(lines, new_range, old_text)
    assert lines == orig_lines


def test_replace_params():
    lines = [None] + orig_text.split("\n")
    orig_lines = list(lines)
    r = SLOC_Range(SLOC(2, 7), SLOC(4, 42))
    new_range, old_text = replace(lines, r, ["-- nothing"])
    new_range, old_text = replace(lines, new_range, old_text)
    assert lines == orig_lines


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
test_replace_fun()
test_replace_params()
