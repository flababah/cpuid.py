import struct
import cpuid

def cpu_vendor(cpu):
	_, b, c, d = cpu(0)
	return struct.pack("III", b, d, c)

def cpu_name(cpu):
	return "".join((struct.pack("IIII", *cpu(0x80000000 + i))
			for i in range(2, 5))).strip()

def is_set(cpu, id, reg_idx, bit):
	regs = cpu(id)

	if (1 << bit) & regs[reg_idx]:
		return "Yes"
	else:
		return "--"

if __name__ == "__main__":
	cpu = cpuid.CPUID()

	print "Vendor ID : %s" % cpu_vendor(cpu)
	print "CPU name  : %s" % cpu_name(cpu)
	print
	print "Vector instructions supported:"
	print "SSE       : %s" % is_set(cpu, 1, 3, 25)
	print "SSE2      : %s" % is_set(cpu, 1, 3, 26)
	print "SSE3      : %s" % is_set(cpu, 1, 2, 0)
	print "SSSE3     : %s" % is_set(cpu, 1, 2, 9)
	print "SSE4.1    : %s" % is_set(cpu, 1, 2, 19)
	print "SSE4.2    : %s" % is_set(cpu, 1, 2, 20)
	print "SSEa      : %s" % is_set(cpu, 0x80000001, 2, 6)
	print "AVX       : %s" % is_set(cpu, 1, 2, 28)
	print "AVX2      : %s" % is_set(cpu, 7, 1, 5)

