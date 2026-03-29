;Program 2 (program2.asm) should define two local variables, n and count, and initialize both to be 0.  
;Then it should prompt the user using a string to enter a value for n, and continually re-prompt them for n until n>0.  
;Once the user has given a valid value of n, it should do the Collatz function in a while loop, printing n each time before changing n, 
;and also adding 1 to the count.  After the loop exits, it should print n (which will now be 1) and then also print the count.\

.data
prompt:  .asciiz "Enter a positive integer n: "
newline: .asciiz "\n"

.text
.globl main
main:

    li t0, 0
    li t1, 0

input_loop:
    PUTS prompt
    GETI t0
    blez t0, input_loop  

collatz_loop:

    PUTI t0
    PUTS newline

    li t2, 1
    beq t0, t2, done

    addi t1, t1, 1

    li t2, 2
    div t3, t0, t2
    mul t3, t3, t2
    sub t4, t0, t3 

    beqz t4, even_case

odd_case:
    li t2, 3
    mul t0, t0, t2
    addi t0, t0, 1
    j collatz_loop

even_case:
    li t2, 2
    div t0, t0, t2
    j collatz_loop

done:
    # print final n (1)
    PUTI t0
    PUTS newline

    # print count
    PUTI t1
    PUTS newline

    HALT