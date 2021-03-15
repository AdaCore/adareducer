def dichotomize(chunks, predicate):
    """Apply dichotomy for actionable chunks.
       Return the chunks which cannot be applied
    """

    for chunk in chunks:
        chunk.do()

    if predicate():
        # yay!
        return []

    if not predicate():
        for chunk in chunks:
            chunk.undo()

        if len(chunks) <= 1:
            return chunks

        mid = int(len(chunks) / 2)
        return dichotomize(chunks[0:mid], predicate) + dichotomize(
            chunks[mid:], predicate
        )
