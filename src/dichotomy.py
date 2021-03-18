def dichotomize(chunks, predicate):
    """Apply dichotomy for actionable chunks.
       Return the chunks which cannot be applied
    """
    # Assume chunks are ordered and process them in
    # reverse order
    for chunk in reversed(chunks):
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
