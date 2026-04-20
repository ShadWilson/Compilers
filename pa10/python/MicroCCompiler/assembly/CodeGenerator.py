import sys
import os
from typing import List

from .CodeObject import CodeObject
from .InstructionList import InstructionList
from .instructions import *
from ..compiler import *
from ..ast import *
from ..ast.visitor.AbstractASTVisitor import AbstractASTVisitor
class CodeGenerator(AbstractASTVisitor):

  def __init__(self):
    self.intRegCount = 1
    self.floatRegCount = 1
    self.intTempPrefix = 't'
    self.floatTempPrefix = 'f'
    self.numCtrlStructs = 0
    self.loopLabel = 0
    self.elseLabel = 0
    self.outLabel = 0
    self.currFunc = None

  def getIntRegCount(self):
    return self.intRegCount

  def getFloatRegCount(self):
    return self.floatRegCount



  def postprocessVarNode(self, node: VarNode) -> CodeObject:
    sym = node.getSymbol()

    co = CodeObject(sym)
    co.lval = True
    co.type = node.getType()

    return co
  
  def postprocessIntLitNode(self, node: IntLitNode) -> CodeObject:
    co = CodeObject()

    temp = self.generateTemp(Scope.Type.INT)
    val = node.getVal()
    # LI t2, 5
    co.code.append(Li(temp, val))
    co.temp = temp
    co.lval = False
    co.type = node.getType()

    return co

  def postprocessFloatLitNode(self, node: FloatLitNode) -> CodeObject:
    co = CodeObject()

    temp = self.generateTemp(Scope.Type.FLOAT)
    val = node.getVal()

    co.code.append(FImm(temp, val))
    co.temp = temp
    co.lval = False
    co.type = node.getType()

    return co

  def postprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:
    co = CodeObject()
    newcode = CodeObject()

    #print("Left: ", left, "Left Type: ", left.type)
    #print("Right: ", right, "Right Type: ", right.type)
    #print("Optype: ", str(node.op))

    optype = str(node.op) # Get string corresponding to the operation (+, -, *, /)
    #Step 1: add code from left child
    
    #Step 1a: check if left child is an lval or rval; if lval, rvalify
    if left.lval == True:
      left = self.rvalify(left) # create new code object, fix this, this is bad?
      #print("Left type after rvalify:", left.type)
    co.code.extend(left.code)

    #Step 2: add code from right child

    if right.lval == True:
      right = self.rvalify(right)
    
    co.code.extend(right.code)
  
    #Step 2a: check if left child is an lval or rval; if lval, rvalify

    #Step 3: generate correct binop.  8 cases for 4 ops, float vs. int. for 4 arithmetic ops.

    if left.type != right.type:
      print("Incompatible types in binary operation!\n")
    
    # Get appropriate new temporary for result of operation
    if left.type == Scope.Type.INT:
      #print("Processing binop with INTs")
      newtemp = self.generateTemp(Scope.Type.INT)
      if optype == "OpType.ADD":
        newcode = Add(left.temp, right.temp, newtemp)
      elif optype == "OpType.SUB":
        newcode = Sub(left.temp, right.temp, newtemp)
      elif optype == "OpType.MUL":
        newcode = Mul(left.temp, right.temp, newtemp)
      elif optype == "OpType.DIV":
        newcode = Div(left.temp, right.temp, newtemp)
      else:
        print("Bad operation in binop!\n")


    elif left.type == Scope.Type.FLOAT:
      newtemp = self.generateTemp(Scope.Type.FLOAT)
      if optype == "OpType.ADD":
        newcode = FAdd(left.temp, right.temp, newtemp)
      elif optype == "OpType.SUB":
        newcode = FSub(left.temp, right.temp, newtemp)
      elif optype == "OpType.MUL":
        newcode = FMul(left.temp, right.temp, newtemp)
      elif optype == "OpType.DIV":
        newcode = FDiv(left.temp, right.temp, newtemp)
      else:
        print("Bad operation in binop!\n")

    else:
      print("Bad type in binary op!\n")


    #Step 4: update temp, lval etc., return code object


    co.code.append(newcode)
    co.lval = False
    co.temp = newtemp
    co.type = left.type
    #print(newcode)
    return co


  def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()  # Step 0
    
    if expr.lval:
      expr = self.rvalify(expr)

    co.code.extend(expr.code) # Add in all the code required to get expr after rvalifying


    if expr.type == Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(Neg(src=expr.temp, dest=temp))
      

    elif expr.type == Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(FNeg(src=expr.temp, dest=temp))

    else:
      raise Exception("Non int/float type in unary op!")

    co.type = expr.type
    co.temp = temp
    co.lval = False 

    return co


  def postprocessAssignNode(self, node: AssignNode, left: CodeObject, right: CodeObject) -> CodeObject:
    co = CodeObject()

    if right.lval:
        right = self.rvalify(right)

    address = self.generateAddrFromVariable(left)

    if address.endswith("(fp)"):
        offset = address.replace("(fp)", "")

        co.code.extend(right.code)

        if left.type == Scope.Type.INT:
            co.code.append(Sw(right.temp, "fp", offset))
        else:
            co.code.append(Fsw(right.temp, "fp", offset))

    else:
        addrTemp = self.generateTemp(Scope.Type.INT)

        co.code.append(La(addrTemp, address))

        co.code.extend(right.code)

        if left.type == Scope.Type.INT:
            co.code.append(Sw(right.temp, addrTemp, '0'))
        else:
            co.code.append(Fsw(right.temp, addrTemp, '0'))

    return co


  def postprocessStatementListNode(self, node: StatementListNode, statements: list) -> CodeObject:
    co = CodeObject()

    for subcode in statements:
      if subcode is None:
        continue
      co.code.extend(subcode.code)

    co.type = None
    return co


  def postprocessReadNode(self, node: ReadNode, var: CodeObject) -> CodeObject:
    co = CodeObject()

    assert(var.isVar())

    if var.type is Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(GetI(temp))
      address = self.generateAddrFromVariable(var)

      if address.endswith("(fp)"):
        offset = address.replace("(fp)", "")
        co.code.append(Sw(temp, "fp", offset))
      else:
        temp2 = self.generateTemp(Scope.Type.INT)
        co.code.append(La(temp2, address))
        co.code.append(Sw(temp, temp2, '0'))

    elif var.type == Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(GetF(temp))

      address = self.generateAddrFromVariable(var)
      if address.endswith("(fp)"):
        offset = address.replace("(fp)", "")
        co.code.append(Fsw(temp, "fp", offset))
      else:
        temp2 = self.generateTemp(Scope.Type.INT)
        co.code.append(La(temp2, address))
        co.code.append(Fsw(temp, temp2, '0'))

    else:
      raise Exception("Bad type in read node")


    return co


  def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()

    if expr.lval and expr.isVar():
      expr = self.rvalify(expr)

    co.code.extend(expr.code)

    if expr.type == Scope.Type.INT:
        co.code.append(PutI(expr.temp))
    elif expr.type == Scope.Type.FLOAT:
        co.code.append(PutF(expr.temp))
    elif expr.type == Scope.Type.STRING:
        co.code.append(PutS(expr.temp))
    else:
        raise Exception("Bad type in write")

    return co
	
  def postprocessCondNode(self, node: CondNode, left: CodeObject, right: CodeObject) -> CodeObject:
    co = CodeObject()

    if left.lval:
        left = self.rvalify(left)
    if right.lval:
        right = self.rvalify(right)

    co.code.extend(left.code)
    co.code.extend(right.code)

    co.temp = (left.temp, right.temp)
    co.type = node.getOp()   # keep original operator
    co.expr_type = left.type

    return co

  def postprocessIfStatementNode(self, node: IfStatementNode, cond: CodeObject, tlist: CodeObject, elist: CodeObject) -> CodeObject:
    self._incrnumCtrlStruct()
    labelnum = self._getnumCtrlStruct()

    then_label = self._generateThenLabel(labelnum)
    else_label = self._generateElseLabel(labelnum)
    done_label = self._generateDoneLabel(labelnum)

    co = CodeObject()

    co.code.extend(cond.code)

    left, right = cond.temp
    op = cond.type

    op_str = str(op)

# branch on FALSE condition → go to else
    if cond.expr_type == Scope.Type.FLOAT:
      result = self.generateTemp(Scope.Type.INT)

      if op_str == "<":
        co.code.append(Flt(left, right, result))
      elif op_str == "<=":
        co.code.append(Fle(left, right, result))
      elif op_str == "==":
        co.code.append(Feq(left, right, result))
      elif op_str == ">":
        co.code.append(Fle(left, right, result))
      elif op_str == ">=":
        co.code.append(Flt(left, right, result))
      else:
        raise Exception(f"Unsupported float condition: {op_str}")

      co.code.append(Bne(result, 'x0', else_label))
    else:
      if op_str == "<":
        co.code.append(Bge(left, right, else_label))
      elif op_str == ">":
        co.code.append(Ble(left, right, else_label))
      elif op_str == "<=":
        co.code.append(Bgt(left, right, else_label))
      elif op_str == ">=":
        co.code.append(Blt(left, right, else_label))
      elif op_str == "==":
        co.code.append(Bne(left, right, else_label))
      elif op_str == "!=":
        co.code.append(Beq(left, right, else_label))
      else:
        raise Exception(f"Unsupported condition: {op_str}")

    # then block
    co.code.extend(tlist.code)
    co.code.append(J(done_label))

    # else block
    co.code.append(Label(else_label))
    if elist:
        co.code.extend(elist.code)

    # done
    co.code.append(Label(done_label))

    return co

  def postprocessWhileNode(self, node: WhileNode, cond: CodeObject, wlist: CodeObject) -> CodeObject:
    self._incrnumCtrlStruct()
    labelnum = self._getnumCtrlStruct()

    loop_label = self._generateLoopLabel(labelnum)
    done_label = self._generateDoneLabel(labelnum)

    co = CodeObject()

    co.code.append(Label(loop_label))

    co.code.extend(cond.code)

    left, right = cond.temp
    op = cond.type
    op_str = str(op)

    if cond.expr_type == Scope.Type.FLOAT:
      result = self.generateTemp(Scope.Type.INT)

      if op_str == "<":
        co.code.append(Flt(left, right, result))
      elif op_str == "<=":
        co.code.append(Fle(left, right, result))
      elif op_str == "==":
        co.code.append(Feq(left, right, result))
      elif op_str == ">":
        co.code.append(Fle(left, right, result))   # flip
      elif op_str == ">=":
        co.code.append(Flt(left, right, result))
      else:
        raise Exception(f"Unsupported float condition: {op_str}")

      co.code.append(Bne(result, 'x0', done_label))

    else:
      if op_str == "<":
        co.code.append(Bge(left, right, done_label))
      elif op_str == ">":
        co.code.append(Ble(left, right, done_label))
      elif op_str == "<=":
        co.code.append(Bgt(left, right, done_label))
      elif op_str == ">=":
        co.code.append(Blt(left, right, done_label))
      elif op_str == "==":
        co.code.append(Bne(left, right, done_label))
      elif op_str == "!=":
        co.code.append(Beq(left, right, done_label))
      else:
        raise Exception(f"Unsupported condition: {op_str}")

    co.code.extend(wlist.code)

    co.code.append(J(loop_label))

    co.code.append(Label(done_label))

    return co


  def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
    co = CodeObject()

    if retExpr.lval is True:
      retExpr = self.rvalify(retExpr)

    co.code.extend(retExpr.code)
    ret_label = self._generateFunctionRetLabel()

    if retExpr.type == Scope.Type.INT:
      co.code.append(Sw(retExpr.temp, "fp", "8"))
    else:
      co.code.append(Fsw(retExpr.temp, "fp", "8"))

    co.code.append(J(ret_label))
    co.type = None
    return co


  def preprocessFunctionNode(self, node: FunctionNode):

    self.currFunc = node.getFuncName()

    self.intRegCount = 1
    self.floatRegCount = 1


  def postprocessFunctionNode(self, node: FunctionNode, body: CodeObject) -> CodeObject:
    '''
    Responsible for actually putting together a function's code
    Step 1: Set up stack frame
    Step 2: Save temporaries
    Step 3: Add in body code (this will include a return node)
    Step 4: Load temporaries
    Step 5: Undo stack frame
    Step 6: Append the RET instruction
    '''

    co = CodeObject()

    entry_label = self._generateFunctionEntryLabel(node.getFuncName())
    ret_label = self._generateFunctionRetLabel()

    co.code.append(Label(entry_label))

    # --- PROLOGUE ---

    # 1. Save old frame pointer (NO sp adjustment before this)
    co.code.append(Sw("fp", "sp", "0"))

    # 2. Set new frame pointer
    co.code.append(Mv("sp", "fp"))

    # 3. Always subtract 4 (matches expected output)
    co.code.append(Addi("sp", "-4", "sp"))

    # 4. Allocate space for locals
    local_size = 0
    for sym in node.getScope().table.values():
        addr = sym.addressToString()
        if addr.startswith("-"):
            offset = int(addr)
            local_size = max(local_size, -offset)

    co.code.append(Addi("sp", f"-{local_size}", "sp"))

    # 5. Save INT temporaries (in order t1, t2, ...)
    for i in range(1, self.intRegCount):
        reg = f"t{i}"
        co.code.append(Sw(reg, "sp", "0"))
        co.code.append(Addi("sp", "-4", "sp"))

    # 6. Save FLOAT temporaries
    for i in range(1, self.floatRegCount):
        reg = f"f{i}"
        co.code.append(Fsw(reg, "sp", "0"))
        co.code.append(Addi("sp", "-4", "sp"))

    # --- BODY ---
    co.code.extend(body.code)

    # --- RETURN LABEL ---
    co.code.append(Label(ret_label))

    # --- RESTORE FLOAT temporaries ---
    for i in reversed(range(1, self.floatRegCount)):
        co.code.append(Addi("sp", "4", "sp"))
        co.code.append(Flw(f"f{i}", "sp", "0"))

    # --- RESTORE INT temporaries ---
    for i in reversed(range(1, self.intRegCount)):
        co.code.append(Addi("sp", "4", "sp"))
        co.code.append(Lw(f"t{i}", "sp", "0"))

    # --- EPILOGUE ---

    co.code.append(Mv("fp", "sp"))
    co.code.append(Lw("fp", "fp", "0"))
    co.code.append(Ret())

    return co


	

  def postprocessFunctionListNode(self, node: FunctionListNode, functions: List[CodeObject]) -> CodeObject:
    '''
    Generate code for the list of functions. This is the "top level" code generation function
    Step 1: Set fp to point to sp
    Step 2: Insert a JR to main
    Step 3: Insert a HALT
    Step 4: Include all the code of the functions
    '''

    co = CodeObject()

    co.code.append(Mv("sp", "fp"))
    co.code.append(Jr(self._generateFunctionEntryLabel("main")))
    co.code.append(Halt())
    co.code.append(Blank())

    # Add code for each of the functions
    for c in functions:
      co.code.extend(c.code)
      co.code.append(Blank())
    
    return co


  def postprocessCallNode(self, node: CallNode, args: List[CodeObject]) -> CodeObject:
    '''
    Responsible for handling when we actually make a function call, for example, something like a = foo(b)
    The call node would be the foo(b) call.
    Step 1: For each argument, insert rvalified code object and push result to stack
    Step 2: Allocate space for return value (what if there isn't one?)
    Step 3: Push ra to stack
    Step 4: JR to function
    Step 5: Pop ra back from stack
    Step 6: Pop return value into fresh temporary
    Step 7: Remove arguments from stack (move sp up, no need to keep these values)
    '''

    co = CodeObject()

    # Step 1: push args (reverse order)
    for arg in args:
        if arg.lval:
            arg = self.rvalify(arg)
        co.code.extend(arg.code)

        if arg.type == Scope.Type.INT:
          co.code.append(Sw(arg.temp, "sp", "0"))
        else:
          co.code.append(Fsw(arg.temp, "sp", "0"))

        co.code.append(Addi("sp", "-4", "sp"))

    # Step 2: allocate space for return value
    co.code.append(Addi("sp", "-4", "sp"))

    # Step 3: push ra
    co.code.append(Sw("ra", "sp", "0"))
    co.code.append(Addi("sp", "-4", "sp"))

    # Step 4: jump
    co.code.append(Jr(self._generateFunctionEntryLabel(node.getFuncName())))

    # Step 5: restore ra
    co.code.append(Addi("sp", "4", "sp"))
    co.code.append(Lw("ra", "sp", "0"))
    co.code.append(Addi("sp", "4", "sp"))

    # Step 6: load return value
    temp = self.generateTemp(node.getType())
    if node.getType() == Scope.Type.INT:
        co.code.append(Lw(temp, "sp", "0"))
    else:
        co.code.append(Flw(temp, "sp", "0"))

    # Step 7: pop return + args
    co.code.append(Addi("sp", str(4 * (len(args))), "sp"))

    co.temp = temp
    co.lval = False
    co.type = node.getType()

    return co


  
  def generateTemp(self, t: Scope.Type) -> str:
    if t == Scope.Type.INT:
      s = self.intTempPrefix + str(self.intRegCount)
      self.intRegCount += 1
      return s
    elif t == Scope.Type.FLOAT:
      s = self.floatTempPrefix + str(self.floatRegCount)
      self.floatRegCount += 1
      return s
    else:
      raise Exception("Generating temp for bad type")



  def rvalify(self, lco : CodeObject) -> CodeObject:
    # If already rval → return
    if not lco.lval:
        return lco

    # If not a variable → already computed
    if not lco.isVar():
        return lco

    co = CodeObject()

    address = self.generateAddrFromVariable(lco)
    if address.endswith("(fp)"):
      offset = address.replace("(fp)", "")
      if lco.type == Scope.Type.INT:
        temp2 = self.generateTemp(Scope.Type.INT)
        co.code.append(Lw(temp2, "fp", offset))
      elif lco.type == Scope.Type.FLOAT:
        temp2 = self.generateTemp(Scope.Type.FLOAT)
        co.code.append(Flw(temp2, "fp", offset))
      else:
        temp2 = None
    else:
      temp1 = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp1, address))

      if lco.type == Scope.Type.INT:
        temp2 = self.generateTemp(Scope.Type.INT)
        co.code.append(Lw(temp2, temp1, '0'))
      elif lco.type == Scope.Type.FLOAT:
        temp2 = self.generateTemp(Scope.Type.FLOAT)
        co.code.append(Flw(temp2, temp1, '0'))
      elif lco.type == Scope.Type.STRING:
        temp2 = temp1

      else:
        raise Exception("Bad type in rvalify!")

    co.type = lco.type
    co.lval = False
    co.temp = temp2

    return co


  def generateAddrFromVariable(self, lco: CodeObject) -> str:
    assert(lco.isVar() is True)

    symbol = lco.getSTE()
    address = symbol.addressToString()  

    if address.startswith("-") or address.isdigit():
      return f"{address}(fp)"
    return address


  def _incrnumCtrlStruct(self):
    self.numCtrlStructs += 1

  def _getnumCtrlStruct(self) -> int:
    return self.numCtrlStructs
  
  def _generateThenLabel(self, num: int) -> str:
    return "then_"+str(num)

  def _generateElseLabel(self, num: int) -> str:
    return "else_"+str(num)

  def _generateLoopLabel(self, num: int) -> str:
    return "loop_"+str(num)

  def _generateDoneLabel(self, num: int) -> str:
    return "out_"+str(num)
  

  
  def _generateFunctionEntryLabel(self, func = None) -> str:
    if func is None:
      return "func_" + self.currFunc
    else:
      return "func_" + func
    
  def _generateFunctionCodeLabel(self, func = None) -> str:
    if func is None:
      return "func_code_" + self.currFunc
    else:
      return "func_code_" + func  


  def _generateFunctionRetLabel(self) -> str:
    return "func_ret_" + self.currFunc