import sys
import os

from .CodeObject import CodeObject
from .InstructionList import InstructionList
from .instructions import *
from ..compiler import *
from ..ast import *
from ..ast.visitor.AbstractASTVisitor import AbstractASTVisitor

class CodeGenerator(AbstractASTVisitor):

  def __init__(self):
    self.intRegCount = 0
    self.floatRegCount = 0
    self.intTempPrefix = 't'
    self.floatTempPrefix = 'f'

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
    '''
    Unary Op Node would be telling us to do -(expr)
    Step 1: Generate blank code object
    Step 2: Get code for expr and rvalify if necessary
    Step 3: Add expr code after rvalifying
    Step 4: Generate instruction to negate 
    Step 5: Update temp/lval of resulting code object
    Step 6: Return it
    '''

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

    co.code.extend(right.code)

    address = self.generateAddrFromVariable(left)
    addrTemp = self.generateTemp(Scope.Type.INT)
    co.code.append(La(addrTemp, address))

    if left.type == Scope.Type.INT:
        co.code.append(Sw(right.temp, addrTemp, '0'))
    elif left.type == Scope.Type.FLOAT:
        co.code.append(Fsw(right.temp, addrTemp, '0'))
    else:
        raise Exception("Invalid type in assignment")

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
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp2, address))
      co.code.append(Sw(temp, temp2, '0'))

    elif var.type == Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(GetF(temp))

      address = self.generateAddrFromVariable(var)
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

  
  def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:

    co = CodeObject()

    if retExpr is not None:
        if retExpr.lval:
            retExpr = self.rvalify(retExpr)

        co.code.extend(retExpr.code)

        # If your convention needs a return register, set it here
        co.temp = retExpr.temp
        co.type = retExpr.type
    co.code.append(Halt())
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
    '''
    Changed type to return string.
    This function is responsible for returning the string that has the address of the variable.
    Right now it can only handle global variables.
    For globals: addresses are raw hex, e.g. 0x20000000
    Locals will be a number relative to the frame pointer
    '''

    assert(lco.isVar() is True)

    symbol = lco.getSTE()   # Get symbol from symbol table
    address = str(symbol.getAddress()) # Get address of variable

    return address
    