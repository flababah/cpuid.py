# -*- coding: utf-8 -*-
#
#     Copyright (c) 2014 Anders Høst
#

import platform
import os
import ctypes
from ctypes import c_uint32, c_long, POINTER, CFUNCTYPE

# Call registers for 64 bit Posix: %rdi, %rsi
_POSIX_64_OPC = [
        0x48, 0x89, 0xf0,  # mov    %rsi,%rax
        0x0f, 0xa2,        # cpuid
        0x89, 0x07,        # mov    %eax,(%rdi)
        0x89, 0x5f, 0x04,  # mov    %ebx,0x4(%rdi)
        0x89, 0x4f, 0x08,  # mov    %ecx,0x8(%rdi)
        0x89, 0x57, 0x0c,  # mov    %edx,0xc(%rdi)
        0xc3               # retq
]

# Call registers for 64 bit Windows: %rcx, %rdx
_WINDOWS_64_OPC = [
        0x48, 0x89, 0xd0,  # mov    %rdx,%rax
        0x48, 0x89, 0xcf,  # mov    %rcx, %rdi
        0x0f, 0xa2,        # cpuid
        0x89, 0x07,        # mov    %eax,(%rdx)
        0x89, 0x5f, 0x04,  # mov    %ebx,0x4(%rdx)
        0x89, 0x4f, 0x08,  # mov    %ecx,0x8(%rdx)
        0x89, 0x57, 0x0c,  # mov    %edx,0xc(%rdx)
        0xc3               # retq
]

is_windows = os.name == "nt"

class CPUID_struct(ctypes.Structure):
    _fields_ = [(r, c_uint32) for r in ("eax", "ebx", "ecx", "edx")]

class CPUID(object):
    def __init__(self):
        if ctypes.sizeof(ctypes.c_voidp) != 8:
            raise SystemError("Only x86_64 supported for now")

        opc = _WINDOWS_64_OPC if is_windows else _POSIX_64_OPC
        code = "".join((chr(x) for x in opc))
        self.r = CPUID_struct()
        size = len(code)

        if is_windows:
            # VirtualAlloc seems to fail under some weird circumstances
            # when ctypes.windll.kernel32 is used. CDLL fixes this.
            self.win = ctypes.CDLL("kernel32.dll")
            self.addr = self.win.VirtualAlloc(None, size, 0x1000, 0x40)
        else:
            self.addr = ctypes.pythonapi.valloc(size)
            ctypes.pythonapi.mprotect(self.addr, size, 1 | 2 | 4)

        assert self.addr
        ctypes.memmove(self.addr, code, size)
        func_type = CFUNCTYPE(None, POINTER(CPUID_struct), c_long)
        self.func_ptr = func_type(self.addr)

    def __call__(self, eax):
        self.func_ptr(self.r, eax)
        return (self.r.eax, self.r.ebx, self.r.ecx, self.r.edx)

    def __del__(self):
        if is_windows:
            self.win.VirtualFree(self.addr, 0, 0x8000)
        elif ctypes.pythonapi:
            # Seems to throw exception when the program ends and
            # pythonapi is cleaned up before the object?
            ctypes.pythonapi.free(self.addr)

if __name__ == "__main__":
    def valid_inputs():
        cpuid = CPUID()
        for eax in (0x0, 0x80000000):
            highest, _, _, _ = cpuid(eax)
            while eax <= highest:
                regs = cpuid(eax)
                yield (eax, regs)
                eax += 1

    print " ".join(x.ljust(8) for x in ("CPUID", "A", "B", "C", "D"))
    for eax, tups in valid_inputs():
        print "%08x" % eax,
        print "%08x " * 4 % tups
