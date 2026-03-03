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
        code.append(f"l{statement.name}")
        return code
    
    if isinstance(statement, PrintNode):
        exprcode = stmtcodegen(statement.expr)
        code.extend(exprcode)
        code.append("p")
        return code


    
    if isinstance(statement, AssignNode):
        exprcode = stmtcodegen(statement.expr)
        code.extend(exprcode)
        code.append(f"s{statement.name}")
        return code
    

    if isinstance(statement, BinOpNode):

        if statement.op == "^":

            if not isinstance(statement.right, IntLitNode):
                raise ValueError("Exponent must be an integer literal")

            exponent = statement.right.value

            if exponent < 0:
                raise ValueError("Negative exponents not supported")

            if exponent == 0:
                code.append("1")
                return code

            # Generate base ONCE
            basecode = stmtcodegen(statement.left)
            code.extend(basecode)

            # Duplicate base (exponent - 1) times
            for _ in range(exponent - 1):
                code.append("d")

            # Multiply them all together
            for _ in range(exponent - 1):
                code.append("*")

            return code

     # All other binary operators
        leftcode = stmtcodegen(statement.left)
        rightcode = stmtcodegen(statement.right)

        code.extend(leftcode)
        code.extend(rightcode)

        if statement.op == "+":
            code.append("+")
        elif statement.op == "-":
            code.append("-")
        elif statement.op == "*":
            code.append("*")
        elif statement.op == "/":
            code.append("/")
        else:
            raise ValueError(f"Unknown operator {statement.op}")

        return code