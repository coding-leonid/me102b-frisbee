import threading

def init():
    global RANGE, SHOULD_EXIT, IMG_SIZE

    # Current range reading
    RANGE = float
    # Flag for telling the serial thread to exit
    SHOULD_EXIT = threading.Event()
    # Image size
    IMG_SIZE = (640, 480)
