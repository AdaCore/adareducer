import os
import libadalang as lal
from src.types import Buffer, infer_or_equal
from src.interfaces import ChunkInterface, StrategyInterface
from src.dichotomy import to_tree, dichototree


class RemoveSubprogram(ChunkInterface):
    def __init__(self, file, node, buffers, units):
        self.file = file
        self.node = node
        self.buffers = buffers

        # Resolve node
        self.decl = node.p_decl_part()
        self.other_file = None

    def do(self):
        num_lines = self.node.sloc_range.end.line - self.node.sloc_range.start.line + 1
        new_text = [""] * num_lines
        self.body_range, self.body_lines = self.buffers[self.file].replace(
            self.node.sloc_range, new_text
        )
        if self.decl is None or not os.path.exists(self.decl.unit.filename):
            return
        self.other_file = self.decl.unit.filename
        if self.other_file not in self.buffers:
            self.buffers[self.other_file] = Buffer(self.other_file)

        num_lines = self.decl.sloc_range.end.line - self.decl.sloc_range.start.line + 1
        new_text = [""] * num_lines
        self.spec_range, self.spec_lines = self.buffers[self.other_file].replace(
            self.decl.sloc_range, new_text
        )

    def undo(self):
        self.buffers[self.file].replace(self.body_range, self.body_lines)
        if self.other_file is not None:
            self.buffers[self.other_file].replace(self.spec_range, self.spec_lines)

    def is_in(self, other):
        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class RemoveSubprograms(StrategyInterface):
    """ Remove subprograms """

    def pred(self):
        for file in self.buffers:
            self.buffers[file].save()
        return self.predicate()

    def run_on_file(self, context, file, predicate):
        self.context = context
        self.predicate = predicate

        self.buffers = {file: Buffer(file)}
        self.units = {file: self.context.get_from_file(file)}

        # List all subprograms in the file

        chunks = []
        for subp in self.units[file].root.findall(lambda x: x.is_a(lal.SubpBody)):
            # Create a chunk for each subprogram
            chunks.append(RemoveSubprogram(file, subp, self.buffers, self.units))

        t = to_tree(chunks)
        return dichototree(t, self.pred)