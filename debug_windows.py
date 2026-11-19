import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

count = 0
def enum_cb(hwnd, extra):
    global count
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        print(f"Title: {buff.value}")
        count += 1
        if count > 15:
            return False
    return True

CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(CMPFUNC(enum_cb), 0)
