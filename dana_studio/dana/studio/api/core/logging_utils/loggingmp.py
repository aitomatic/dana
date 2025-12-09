# pylint: disable=wildcard-import, invalid-name
# type: ignore
# ruff: noqa
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
import platform
import time
from . import ipc

if platform.system().lower() == "windows":

    class _IncrementalLock(ipc.Lock):
        def try_lock(self, value):
            self.acquire()
            return True

        def release_lock(self, value):
            self.release()

else:

    class _IncrementalLock:
        def __init__(self, name):
            self.name = name
            self.lock = None

        def try_lock(self, value):
            if self.lock is not None:
                return False
            self.lock = ipc.Lock(self.name)
            self.lock.acquire()
            old_value = self.lock.handle.read()
            if value <= old_value:
                self.lock.release()
                self.lock = None
                return False
            return True

        def release_lock(self, value):
            if self.lock is None:
                return
            with open(self.lock.filename, "w") as f:
                f.write(value)
            self.lock.release()
            self.lock = None


class MPRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, mode="a", maxBytes=0, backupCount=0, encoding=None, delay=0):
        self.mplock_name = filename.replace("/", "_").replace("\\", "_")
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

    def doRollover(self):
        mplock = ipc.Lock(self.mplock_name)
        mplock.acquire()
        if not self.prepareRollover():
            mplock.release()
            return
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d" % (self.baseFilename, i)
                dfn = "%s.%d" % (self.baseFilename, i + 1)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        mplock.release()
        self.stream = self._open()

    def prepareRollover(self):
        if self.stream is not None:
            self.flush()
            self.stream.close()
            self.stream = None
        self.stream = self._open()
        if self.maxBytes > 0:
            self.stream.seek(0, 2)
            if self.stream.tell() >= float(self.maxBytes) * 0.99:
                return True
        return False


class MPTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename,
        when="h",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
    ):
        self.mplock_name = filename.replace("/", "_").replace("\\", "_")
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)

    def computeRollover(self, currentTime):
        result = int(super().computeRollover(currentTime))
        if self.when == "S":
            result = result
        elif self.when == "M":
            result = result / 60 * 60
        elif self.when == "H":
            result = result / 3600 * 3600
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        formattedTime = time.strftime(self.suffix, timeTuple)
        mplock = _IncrementalLock(self.mplock_name)
        if mplock.try_lock(formattedTime):
            dfn = self.baseFilename + "." + formattedTime
            if os.path.exists(self.baseFilename) and not os.path.exists(dfn):
                os.rename(self.baseFilename, dfn)
                if self.backupCount > 0:
                    for s in self.getFilesToDelete():
                        os.remove(s)
            mplock.release_lock(formattedTime)

        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        if (self.when == "MIDNIGHT" or self.when.startswith("W")) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt -= 3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt += 3600
        self.rolloverAt = newRolloverAt
