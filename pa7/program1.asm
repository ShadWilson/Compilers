;Program 1 (program1.asm) should define two global variables, a and b, and three strings, "a is less than b", "a is equal to b", and "a is greater than b".  
;It should read the value of both variables from the user (using GETI), and then using branch instructions, print precisely one of the strings based on whether 
;a<b, a=b, or a>b.  

.text
.globl main
main:

;a
GETI t0
;b
GETI t1

# compare
BLT t0, t1, less
BEQ t0, t1, equal
J greater

less:
LA t0, 0x10000000
PUTS t0
J end

equal:
LA t0, 0x10000004
PUTS t0
J end

greater:
LA t0, 0x10000008
PUTS t0
J end

end:
HALT

.section .strings
0x10000000 "a is less than b\n"
0x10000004 "a is equal to b\n"
0x10000008 "a is greater than b\n"