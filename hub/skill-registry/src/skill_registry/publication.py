"""Kernel no-clobber directory publication for supported local clients."""

import ctypes
import errno
import os
import sys
from pathlib import Path


def publish_directory(stage: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        function = libc.renamex_np
        function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        code = function(os.fsencode(stage), os.fsencode(destination), 4)
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        function = libc.renameat2
        function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                             ctypes.c_uint]
        code = function(-100, os.fsencode(stage), -100, os.fsencode(destination), 1)
    else:
        raise OSError("Pinned installation requires macOS renamex_np or Linux renameat2")
    if code:
        number = ctypes.get_errno()
        if number in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(f"Installation already exists: {destination}")
        raise OSError(number, os.strerror(number), str(destination))
