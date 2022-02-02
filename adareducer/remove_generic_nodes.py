import os
import libadalang as lal
from adareducer.types import Buffer, infer_or_equal
from adareducer.interfaces import ChunkInterface, StrategyInterface
from adareducer.dichotomy import to_tree, dichototree


DEBUG = False


class AbstractRemoveNode(object):
    def __init__(self, node, buffers):
        self.node = node
        self.buffers = buffers
        self.locations_to_remove = []
        # a list which contains
        #  - (file, range, replacement_lines)

        self.locations_removed = []
        # a list which contains
        #  - (file, range, replacement_lines)

    def find_locations_to_remove(self):
        """Fill self.locations_to_remove with the locations to remove, based
           on self.node"""
        pass

    def add_location_to_replace_with_empty(self, node):
        if node is None:
            return
        file = node.unit.filename
        if file not in self.buffers:
            self.buffers[file] = Buffer(file)
        num_lines = node.sloc_range.end.line - node.sloc_range.start.line + 1
        self.locations_to_remove.append((file, node.sloc_range, [""] * num_lines))

    def apply(self, locations_list, to_list):
        """Apply the changes in the given list.
           Store the reverse changes in to_list."""

        for file, range, replacement_lines in locations_list:
            if DEBUG:
                print(f"{file}: replacing {range}")
            r, l = self.buffers[file].replace(range, replacement_lines)

            to_list.append((file, r, l))

    def do(self):
        self.locations_to_remove = []
        self.find_locations_to_remove()
        self.apply(self.locations_to_remove, self.locations_removed)
        self.locations_to_remove = []

    def undo(self):
        bin = []
        self.apply(self.locations_removed, bin)
        self.locations_removed = []

    def is_in(self, other):
        return infer_or_equal(
            other.node.sloc_range.start, self.node.sloc_range.start
        ) and infer_or_equal(self.node.sloc_range.end, other.node.sloc_range.end)


class RemovePackage(AbstractRemoveNode):
    def __init__(self, node, buffers):
        super().__init__(node, buffers)

    def find_locations_to_remove(self):
        self.add_location_to_replace_with_empty(self.node)
        decl = self.node.p_decl_part()
        if decl is None:
            return
        if decl.is_a(lal.GenericPackageInternal):
            decl = decl.parent
        self.add_location_to_replace_with_empty(decl)


class RemovePackages(StrategyInterface):
    """ Remove package bodies """

    def save(self):
        for file in self.buffers:
            self.buffers[file].save()

    def run_on_file(self, context, file, predicate):
        self.context = context
        self.predicate = predicate

        self.buffers = {file: Buffer(file)}
        unit = self.context.get_from_file(file)

        if unit.root is None:
            return

        # List all subprograms in the file

        chunks = []
        for pbody in unit.root.findall(lambda x: x.is_a(lal.PackageBody)):
            # Create a chunk for each subprogram
            chunks.append(RemovePackage(pbody, self.buffers))

        t = to_tree(chunks)
        r = dichototree(t, predicate, self.save)
        return r


class RemoveAspect(AbstractRemoveNode):
    def __init__(self, node, buffers):
        super().__init__(node, buffers)

    def find_locations_to_remove(self):
        self.add_location_to_replace_with_empty(self.node)


class RemoveAspects(StrategyInterface):
    """ Remove aspects"""

    def save(self):
        for file in self.buffers:
            self.buffers[file].save()

    def run_on_file(self, context, file, predicate):
        self.context = context
        self.predicate = predicate

        self.buffers = {file: Buffer(file)}
        unit = self.context.get_from_file(file)

        if unit.root is None:
            return

        # List all aspects in the file

        chunks = []
        for pbody in unit.root.findall(lambda x: x.is_a(lal.AspectSpec)):
            # Create a chunk for each aspect
            chunks.append(RemoveAspect(pbody, self.buffers))

        t = to_tree(chunks)
        r = dichototree(t, predicate, self.save)
        return r