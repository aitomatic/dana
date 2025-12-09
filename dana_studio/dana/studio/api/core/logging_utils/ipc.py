import platform

if platform.system().lower() == "windows":
    import win32api
    import win32event

    class Lock:
        def __init__(self, name):
            self.name = name
            self.handle = win32event.CreateMutex(None, 0, self.name)
            self.locked = False

        def __del__(self):
            if self.locked:
                self.release()
            win32api.CloseHandle(self.handle)

        def acquire(self):
            win32event.WaitForSingleObject(self.handle, win32event.INFINITE)
            self.locked = True

        def release(self):
            win32event.ReleaseMutex(self.handle)
            self.locked = False

else:
    import os
    import fcntl

    class Lock:
        def __init__(self, name):
            self.filename = os.path.join("/tmp/", name)
            self.handle = open(self.filename, "a+")
            self.locked = False

        def __del__(self):
            if self.locked:
                self.release()
            self.handle.close()

        # Bitwise OR fcntl.LOCK_NB if you need a non-blocking lock
        def acquire(self):
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
            self.locked = True

        def release(self):
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.locked = False
