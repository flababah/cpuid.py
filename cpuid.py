# -*- coding: utf-8 -*-
#
#     Copyright (c) 2014 Anders Høst
#

import platform
import os
from ctypes import c_uint32, c_long, POINTER
from ctypes import pythonapi, memmove, CFUNCTYPE, Structure

# Input registers for 64bit Posix: %rdi, %rsi
_POSIX_64_OPC = [
        0x48, 0x89, 0xf0,  # mov    %rsi,%rax
        0x0f, 0xa2,        # cpuid
        0x89, 0x07,        # mov    %eax,(%rdi)
        0x89, 0x5f, 0x04,  # mov    %ebx,0x4(%rdi)
        0x89, 0x4f, 0x08,  # mov    %ecx,0x8(%rdi)
        0x89, 0x57, 0x0c,  # mov    %edx,0xc(%rdi)
        0xc3               # retq
]

class CPUID_struct(Structure):
    _fields_ = [(r, c_uint32) for r in ("eax", "ebx", "ecx", "edx")]

class CPUID(object):
    def __init__(self):
        if os.name != "posix" or platform.machine() != "x86_64":
            raise SystemError("Platform not supported")

        code = "".join((chr(x) for x in _POSIX_64_OPC))
        self.r = CPUID_struct()
        size = len(code)

        self.addr = pythonapi.valloc(size)
        pythonapi.mprotect(self.addr, size, 1 | 2 | 4)
        memmove(self.addr, code, size)
        func_type = CFUNCTYPE(None, POINTER(CPUID_struct), c_long)
        self.func_ptr = func_type(self.addr)

    def __call__(self, eax):
        self.func_ptr(self.r, eax)
        return (self.r.eax, self.r.ebx, self.r.ecx, self.r.edx)

    def __del__(self):
        # Seems to throw exception when the program ends and pythonapi
        # is cleaned up before the object?
        if pythonapi:
            pythonapi.free(self.addr)

if __name__ == "__main__":
    def valid_inputs():
        cpuid = CPUID()
        for eax in (0x0, 0x80000000):
            highest, _, _, _ = cpuid(eax)
            while eax <= highest:
                regs = cpuid(eax)
                yield (eax, regs)
                eax += 1
        del cpuid

    print " ".join(x.ljust(8) for x in ("CPUID", "A", "B", "C", "D"))
    for eax, tups in valid_inputs():
        print "%08x" % eax,
        print "%08x " * 4 % tups

