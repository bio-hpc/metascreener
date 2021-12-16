
logging = None

def init_logging():
    global logging
    logging = ""

def log(msg):
    global logging
    logging += msg

def write_log(fname):
    global logging
    with open(fname, 'w') as f:
        f.write(logging)
