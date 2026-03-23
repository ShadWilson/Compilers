.section .text

MV fp, sp
JR func_main
HALT

func_main:
SW fp, 0(sp)
MV fp, sp
ADDI sp, sp, -4

ADDI sp, sp, -4

GETI t0
LA t1, 0x20000000
SW t0, 0(t1)

GETI t2
SW t2, -4(fp)

LA t3, 0x20000000
PUTI t3

LW t4, -4(fp)
PUTI t4

ADDI sp, sp, 4

ADDI sp, sp, 4
MV sp, fp
RET