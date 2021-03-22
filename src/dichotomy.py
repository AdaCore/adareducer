from src.gui import log


def dichotomize(chunks, predicate):
    """Apply dichotomy for actionable chunks
    .
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

    if predicate():
        # Yay! all chunks could be actioned
        return (chunks, [])
    else:
        # Not all chunks could not be actioned...
        for chunk in chunks:
            chunk.undo()
        if len(chunks) <= 1:
            # We've dichotomized as much as we could.
            return ([], chunks)

        # We've got to dichotomize more
        mid = int(len(chunks) / 2)

        actioned_l, not_actioned_l = dichotomize(chunks[0:mid], predicate)
        actioned_r, not_actioned_r = dichotomize(chunks[mid:], predicate)

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


def dichototree(chunks_tree, predicate):
    """Dichotomize the tree, first attempting the topmost level,
       then descending the exploration as levels fail.
    """
    to_test = list(chunks_tree.children)
    level = 0
    while to_test:
        level += 1
        actioned, not_actioned = dichotomize(to_test, predicate)
        log(
            f"{level * ' '} level {level}: {len(actioned)} actioned, "
            + f"{len(not_actioned)} not actioned"
        )
        to_test = []

        for x in not_actioned:
            for c in x.children:
                to_test.append(c)

    predicate()
