from acdcast import *

class InstructionList:

    def __init__(self):

        self.instructions = []

    def append(self, instruction: str):

        self.instructions.append(instruction)

    def extend(self, newinstructions: "InstructionList"):
        
        self.instructions.extend(newinstructions.instructions)

    def __iter__(self):
        return iter(self.instructions)




def codegenerator(program: list[ASTNode]) -> InstructionList:

    code = InstructionList()

    for statement in program:

        newcode = stmtcodegen(statement)
        code.extend(newcode)

    return code
    

def stmtcodegen(statement: ASTNode) -> InstructionList:

    code = InstructionList()

    if isinstance(statement, IntDclNode):
        return code


    if isinstance(statement, IntLitNode):
        code.append(str(statement.value))
        return code



    if isinstance(statement, VarRefNode):
        code.append(f"l{statement.varname}")
        return code
    
    if isinstance(statement, PrintNode):
        #exprcode = stmtcodegen(statement.varname)
        #code.extend(exprcode)
        code.append(f"l{statement.varname}")
        code.append("p")
        return code


    
    if isinstance(statement, AssignNode):
        exprcode = stmtcodegen(statement.expr)
        code.extend(exprcode)
        code.append(f"s{statement.varname}")
        return code
    

    if isinstance(statement, BinOpNode):

        # LEFT FIRST
        leftcode = stmtcodegen(statement.left)
        code.extend(leftcode)

        # ---------- EXPONENT ----------
        if statement.optype == TokenType.EXPONENT:

            # variable exponent → just use ^
            if not isinstance(statement.right, IntLitNode):
                rightcode = stmtcodegen(statement.right)
                code.extend(rightcode)
                code.append("^")
                return code

            exponent = statement.right.value

            if exponent < 0:
                raise ValueError("Negative exponents not supported")

            if exponent == 0:
                code = InstructionList()
                code.append("1")
                return code

            # base already on stack once
            for _ in range(exponent - 1):
                code.append("d")   # duplicate

            for _ in range(exponent - 1):
                code.append("*")   # multiply

            return code

        # ---------- NORMAL BINOPS ----------
        rightcode = stmtcodegen(statement.right)
        code.extend(rightcode)

        if statement.optype == TokenType.PLUS:
            code.append("+")
        elif statement.optype == TokenType.MINUS:
            code.append("-")
        elif statement.optype == TokenType.TIMES:
            code.append("*")
        elif statement.optype == TokenType.DIVIDE:
            code.append("/")
        elif statement.optype == TokenType.MOD:
            code.append("%")
        else:
            raise ValueError(f"Unknown operator {statement.optype}")

        return code
    if isinstance(statement, UnaryOpNode):
        operandcode = stmtcodegen(statement.right)
        code.extend(operandcode)

        if statement.optype == TokenType.SQRT:
            code.append("v")
        else:
            raise ValueError(f"Unknown unary operator {statement.optype}")

        return code