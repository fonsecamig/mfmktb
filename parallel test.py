import threading
from time import sleep
from pandas import DataFrame


def f(s):
    global n
    while True:
        n.loc[0] += 1
        sleep(s)


def g(s):
    global n
    while True:
        sleep(s)
        n.loc[1] += 1
        print(n)


n = DataFrame([5, 6, 7])

if __name__ == '__main__':
    t1 = threading.Thread(target=f, args=(10,))
    t2 = threading.Thread(target=g, args=(2,))

    t1.start()
    t2.start()

    t1.join()
    t2.join()
