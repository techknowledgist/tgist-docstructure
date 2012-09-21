
def connect(objects):
    """Turn the objects list into a linked list."""
    for i in range(len(objects)-1):
        obj = objects[i]
        next_obj = objects[i+1]
        obj.next = next_obj
        next_obj.previous = obj
    if objects:
        # just to make sure that there is a previous and next on each object
        objects[0].previous = None
        objects[-1].next = None

