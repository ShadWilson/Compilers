;Program 2 (program2.asm) should define two local variables, n and count, and initialize both to be 0.  
;Then it should prompt the user using a string to enter a value for n, and continually re-prompt them for n until n>0.  
;Once the user has given a valid value of n, it should do the Collatz function in a while loop, printing n each time before changing n, 
;and also adding 1 to the count.  After the loop exits, it should print n (which will now be 1) and then also print the count.\

.text
.globl main
main:
LI t0, 0
LI t1, 0

input_loop:
LA t0, 0x10000000
PUTS t0
GETI t0
BLEZ t0, input_loop  

collatz_loop:
PUTI t0
LA t0, 0x10000004
PUTS t0

LI t2, 1
BEQ t0, t2, done

ADDI t1, t1, 1

LI t2, 2
DIV t3, t0, t2
MUL t3, t3, t2
SUB t4, t0, t3 

BEQZ t4, even_case

odd_case:
LI t2, 3
MUL t0, t0, t2
ADDI t0, t0, 1
J collatz_loop

even_case:
LI t2, 2
DIV t0, t0, t2
J collatz_loop

done:
# print final n (1)
PUTI t0
LA t0, 0x10000004
PUTS t0

# print count
PUTI t1
LA t0, 0x10000004
PUTS t0

HALT

.section .strings
0x10000000 "Enter a positive integer n: "
0x10000004 "\n"