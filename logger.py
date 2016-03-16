import time


class Logger:
    name = ''

    def __init__(self, filename):
        self.name = filename
        self.log = open(filename, 'a')

    def write(self, message):
        try:
            self.log.write(time.strftime("%m/%d/%y %H:%M:%S") + " " + str(time.time()) + "\t" + message + "\n")
        except UnicodeEncodeError:
            self.log.write(time.strftime("%m/%d/%y %H:%M:%S") + " " + str(time.time()) + "\t" + message.encode('utf-8') + "\n")
        self.log.flush()

    def flush(self):
        self.log.flush()