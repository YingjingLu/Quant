import threading
import multiprocessing as mp
sem = threading.Lock()

import time
class GB(object):
    def __init__(self):
        self.x = 0

    def increment(self):
        if self.x == 5:
            self.x = 0
        else:
            self.x += 1

gb = GB()
def worker(gb):
    try:
        print("Locked")
        gb.increment()
        time.sleep(2)
        print ("gb: ", gb.x)

    finally:
        print("Released")

if __name__ == "__main__":
    jobs = []

    for i in range(5):
        p = mp.Process(target=worker, args = (gb,))

        jobs.append(p)
        p.start()

