import ast

from visitors.BottomLevelProgram import BottomLevelProgram

LabeledInstruction = tuple[str, str]
GLOBALVAR = "globalVar"
LOCALVAR = "localVar"

class TopLevelProgram(ast.NodeVisitor):
    """We support assignments and input/print calls"""
    
    def __init__(self, entry_point, globalRenamedVariables, localRenamedVariables, returns, stackMemory) -> None:
        super().__init__()
        self.__instructions = list()
        self.__record_instruction('NOP1', label=entry_point)
        self.__should_save = True
        self.__current_variable = None
        self.__elem_id_while = 0
        self.__elem_id_if = 0
        self.__processedConstants = []
        self.__globalRenamedVariables = globalRenamedVariables
        self.__localRenamedVariables = localRenamedVariables
        self.__functions = []
        self.__stackMemory = stackMemory
        self.__typeOfVar = None
        self.__returns = returns


    def finalize(self):
        self.__instructions.append((None, '.END'))
        return self.__instructions

    ####
    ## Handling Assignments (variable = ...)
    ###

    def visit_Assign(self, node):
        # remembering the name of the target     
        if node.targets[0].id in self.__globalRenamedVariables:
            self.__current_variable = self.__globalRenamedVariables[node.targets[0].id]
            self.__typeOfVar = GLOBALVAR
        else:
            self.__current_variable = self.__localRenamedVariables[node.targets[0].id]
            self.__typeOfVar = LOCALVAR

        # visiting the left part, now knowing where to store the result
        self.visit(node.value)
        if self.__should_save:

            if self.__typeOfVar == GLOBALVAR:
                self.__record_instruction(f'STWA {self.__current_variable},d')
            else:
                self.__record_instruction(f'STWA {self.__current_variable},s')

        else:
            self.__should_save = True
        self.__current_variable = None


    def visit_Constant(self, node): 

        # checks to see if node within while loop
        inWhile = self.__inWhile(node)

        # if program has already seen the variable, not in a while loop, and is global, then skip instantiation
        if (self.__current_variable not in self.__processedConstants) and (inWhile == False) and (self.__typeOfVar == GLOBALVAR):    # ignores store
            self.__processedConstants.append(self.__current_variable)
            self.__should_save = False
        else:  # goes to store
            self.__record_instruction(f'LDWA {node.value},i')

    
    def visit_Name(self, node):
        if self.__typeOfVar == GLOBALVAR:
            self.__record_instruction(f'LDWA {self.__globalRenamedVariables[node.id]},d')
        else: 
            self.__record_instruction(f'LDWA {self.__localRenamedVariables[node.id]},s')
        

    def visit_BinOp(self, node):
        self.__access_memory(node.left, 'LDWA')
        if isinstance(node.op, ast.Add):
            self.__access_memory(node.right, 'ADDA')
        elif isinstance(node.op, ast.Sub):
            self.__access_memory(node.right, 'SUBA')
        else:
            raise ValueError(f'Unsupported binary operator: {node.op}')

    def visit_Call(self, node):
        match node.func.id:
            case 'int': 
                # Let's visit whatever is casted into an int
                self.visit(node.args[0])
            case 'input':
                # We are only supporting integers for now
                if self.__typeOfVar == GLOBALVAR:
                    self.__record_instruction(f'DECI {self.__current_variable},d')
                    self.__should_save = False # DECI already save the value in memory
                else:
                    self.__record_instruction(f'DECI {self.__current_variable},s')
                    self.__should_save = False # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                if self.__typeOfVar == GLOBALVAR:
                    self.__record_instruction(f'DECO {self.__globalRenamedVariables[node.args[0].id]},d')
                else:
                    self.__record_instruction(f'DECO {self.__localRenamedVariables[node.args[0].id]},s')
            case _:
                # create call with name of function
                if (node.func.id in self.__functions):
                    self.__record_instruction(f'CALL {node.func.id}')
                else:
                    raise ValueError(f'Unsupported function call: {node.func.id}')

    ####
    ## Handling While loops (only variable OP variable)
    ####

    def visit_While(self, node):
        loop_id = self.__identifyWhile()
        inverted = {
            ast.Lt:  'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT', # '>=' in the code means we branch if '<'
            ast.Eq: 'BRNE',    # '==' in the code means we branch if '!='
            ast.NotEq: 'BREQ'   # '!=' in the code means we branch if '=='
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'wh_{loop_id}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # print("node test comparators: ", node.test.comparators[0])
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_wh_{loop_id}')
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'BR wh_{loop_id}')
        # Sentinel marker for the end of the loop
        self.__record_instruction(f'NOP1', label = f'end_wh_{loop_id}')


    def visit_If(self, node):
        loop_id = self.__identifyIf()
        inverted = {
            ast.Lt:  'BRGE',    # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT',    # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE',    # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT',    # '>=' in the code means we branch if '<'
            ast.Eq: 'BRNE',    # '==' in the code means we branch if '!='
            ast.NotEq: 'BREQ'   # '!=' in the code means we branch if '=='
        }

        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'if_{loop_id}')
        
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} else_{loop_id}')
        
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        # mark the end of the if statement
        self.__record_instruction(f'BR end_if_{loop_id}')
        
        # Begin the else statement
        self.__record_instruction(f'NOP1', label = f'else_{loop_id}')

        # Visit all content in the 'else'. If there is an elif, 
        # this will recursively call visit_If().
        for contents in node.orelse:
            self.visit(contents)

        # Mark the end of the else statement
        self.__record_instruction(f'BR end_if_{loop_id}')

        # Sentinel marker for the end of the if else block
        self.__record_instruction(f'NOP1', label = f'end_if_{loop_id}')

    ####
    ## Not handling function calls 
    ####

    def visit_FunctionDef(self, node):

        self.__record_instruction(f'NOP1', label = f'{node.name}')
        self.__functions.append(node.name)

        self.__record_instruction(f'SUBSP {self.__stackMemory},i')

        for contents in node.body:
            self.visit(contents)
        
        self.__record_instruction(f'ADDSP {self.__stackMemory},i')
        self.__record_instruction(f'RET')


    def visit_Return(self, node):

        try:
            self.__record_instruction(f'LDWA {node.value.id},s')
            self.__record_instruction(f'STWA {self.__returns.pop()[0]},s')
        except:
            pass


    ####
    ## Helper functions to 
    ####

    def __record_instruction(self, instruction, label = None):
        self.__instructions.append((label, instruction))

    def __access_memory(self, node, instruction, label = None):
        if isinstance(node, ast.Constant):
            self.__record_instruction(f'{instruction} {node.value},i', label)
        else:
            if node.id in self.__globalRenamedVariables:
                self.__record_instruction(f'{instruction} {self.__globalRenamedVariables[node.id]},d', label) 
            else:
                self.__record_instruction(f'{instruction} {self.__localRenamedVariables[node.id]},s', label)

    def __identifyWhile(self):
        result = self.__elem_id_while
        self.__elem_id_while = self.__elem_id_while + 1
        return result

    def __identifyIf(self):
        result = self.__elem_id_if
        self.__elem_id_if = self.__elem_id_if + 1
        return result

    def __inWhile(self, node):
        resultList = []
        currNode = node

        # check node lineage until reaching root node
        while True:
            try:
                resultList.append(currNode.parent)
                currNode = currNode.parent
            except:
                break 

        # if there is a while node in the lineage, return true
        if any(isinstance(i, ast.While) for i in resultList):
            return True
        else:
            return False