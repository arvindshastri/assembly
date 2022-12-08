import ast

class LocalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the local assignments
    """
    
    def __init__(self, root_node, renamedGlobalVariables) -> None:
        super().__init__()
        self.root_node = root_node
        self.results = set()
        self.renamedVariables = {}
        self.renamedGlobalVariables = renamedGlobalVariables  
        self.renamedVariableConstant = 1
        self.renamedReturnConstant = 1 
        self.returns = []
            

    def visit_FunctionDef(self, node):

        varsForFunc = 0

        for content in node.body:

            if isinstance(content, ast.Assign):
                if len(content.targets) != 1:
                    raise ValueError("Only unary assignments are supported")

                if content.targets[0].id in self.renamedVariables:
                    pass
                else:

                    # create randomly defined local variable for symbol table

                    if len(content.targets[0].id) > 8:
                        renamed = "ddd" + str(self.renamedVariableConstant)
                        self.renamedVariableConstant += 1
                        self.renamedVariables[content.targets[0].id] = renamed
                    else:
                        self.renamedVariables[content.targets[0].id] = content.targets[0].id

                if any(self.renamedVariables[content.targets[0].id] == i[0] for i in self.results):  # if we've already seen it
                    pass 
                else:
                    if isinstance(content.value, ast.Constant):
                        self.results.add((self.renamedVariables[content.targets[0].id], content.value.value))
                    else:
                        self.results.add((self.renamedVariables[content.targets[0].id], None))
                    
                    varsForFunc += 1
            

        # since each function needs one return value, generate random return variable
        returnName = "rrr" + str(self.renamedReturnConstant)
        self.renamedReturnConstant += 1
        self.returns.append((returnName, varsForFunc*2 + 2))
