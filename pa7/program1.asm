;Program 1 (program1.asm) should define two global variables, a and b, and three strings, "a is less than b", "a is equal to b", and "a is greater than b".  
;It should read the value of both variables from the user (using GETI), and then using branch instructions, print precisely one of the strings based on whether 
;a<b, a=b, or a>b.  

.data
msg_lt: .asciiz "a is less than b\n"
msg_eq: .asciiz "a is equal to b\n"
msg_gt: .asciiz "a is greater than b\n"

.text
.globl main
main:

    ;a
    GETI t0
    ;b
    GETI t1

    # compare
    blt t0, t1, less
    beq t0, t1, equal
    j greater

less:
    PUTS msg_lt
    j end

equal:
    PUTS msg_eq
    j end

greater:
    PUTS msg_gt

end:
    HALT