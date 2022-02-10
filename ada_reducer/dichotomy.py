from ada_reducer.gui import log
from ada_reducer.types import Checkpoint

def dichotomize(chunks, predicate, save):
    """Apply dichotomy for actionable chunks

       Return a tuple
          (chunks that could be actioned,
           chunks that could not be actioned)
    """
    # Action all chunks

    # Assume chunks are ordered and process them in
    # reverse order (for the case where chunks are nested
    # in each other or modify line numbers)
    for chunk in reversed(chunks):
        chunk.do()
    save()

    if predicate():
        # Yay! all chunks could be actioned
        return (chunks, [])
    else:
        # Not all chunks could not be actioned...
        for chunk in chunks:
            chunk.undo()
        save()
        if len(chunks) <= 1:
            # We've dichotomized as much as we could.
            return ([], chunks)

        # We've got to dichotomize more
        mid = int(len(chunks) / 2)

        actioned_l, not_actioned_l = dichotomize(chunks[0:mid], predicate, save)
        actioned_r, not_actioned_r = dichotomize(chunks[mid:], predicate, save)

        return (actioned_l + actioned_r, not_actioned_l + not_actioned_r)

def dichotomize_buffers(chunks, predicate, buffers):
    """Apply dichotomy for actionable chunks

       Return a tuple
          (chunks that could be actioned,
           chunks that could not be actioned)
    """
    # Action all chunks

    with Checkpoint(buffers) as changes:
        # Assume chunks are ordered and process them in
        # reverse order (for the case where chunks are nested
        # in each other or modify line numbers)

        for chunk in reversed(chunks):
            chunk.do()

        for buf in buffers:
            buf.save()

        if predicate():
            changes.accept()
            # Yay! all chunks could be actioned
            return (chunks, [])
        else:
            changes.discard()

            for buf in buffers:
                buf.save()

            if len(chunks) <= 1:
                # We've dichotomized as much as we could.
                return ([], chunks)

            # We've got to dichotomize more
            mid = int(len(chunks) / 2)

            actioned_l, not_actioned_l = dichotomize_buffers(chunks[0:mid], predicate, buf)
            actioned_r, not_actioned_r = dichotomize_buffers(chunks[mid:], predicate, buf)

            return (actioned_l + actioned_r, not_actioned_l + not_actioned_r)


class TreeNode(object):
    def __init__(self, element):
        self.element = element  # non-leaf nodes may have None as element
        self.children = []

    def do(self):
        if self.element is not None:
            self.element.do()

    def undo(self):
        if self.element is not None:
            self.element.undo()

    def debugstr(self, indent=""):
        return (
            f"{self.element}"
            + "\n"
            + "\n".join([indent + x.debugstr(indent + "### ") for x in self.children])
        )

    def __str__(self):
        return self.debugstr()


def to_tree(chunks):
    """Take a list of chunks and return a tree of them.
       chunks must have a is_in() function.
    """
    result = TreeNode(None)

    def place_in(root, candidate):
        for child in root.children:
            if candidate.element.is_in(child.element):
                return place_in(child, candidate)
        root.children.append(candidate)

    for c in chunks:
        place_in(result, TreeNode(c))

    return result


def dichototree(chunks_tree, predicate, save):
    """Dichotomize the tree, first attempting the topmost level,
       then descending the exploration as levels fail.
    """
    to_test = list(chunks_tree.children)
    level = 0
    while to_test:
        level += 1
        actioned, not_actioned = dichotomize(to_test, predicate, save)
        log(
            f"{level * ' '} level {level}: {len(actioned)} actioned, "
            + f"{len(not_actioned)} not actioned"
        )
        to_test = []

        for x in not_actioned:
            for c in x.children:
                to_test.append(c)


def dichototree_buffers(chunks_tree, predicate, buffers):
    """Dichotomize the tree, first attempting the topmost level,
       then descending the exploration as levels fail.

       buffers is a set of buffers
    """
    to_test = list(chunks_tree.children)
    level = 0
    while to_test:
        level += 1
        actioned, not_actioned = dichotomize_buffers(to_test, predicate, buffers)
        log(
            f"{level * ' '} level {level}: {len(actioned)} actioned, "
            + f"{len(not_actioned)} not actioned"
        )
        to_test = []

        for x in not_actioned:
            for c in x.children:
                to_test.append(c)
