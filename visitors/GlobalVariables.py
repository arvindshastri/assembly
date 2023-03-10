import ast

class GlobalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the global (top-level) assignments
    """
    
    def __init__(self, root_node) -> None:
        super().__init__()
        self.root_node = root_node
        self.childParent(self.root_node)
        self.results = set()
        self.renamedVariables = {}
        self.renamedVariableConstant = 1


    def visit_Assign(self, node):  

        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")

        if node.targets[0].id in self.renamedVariables:
            pass
        else:
            #  generate a arbitrarily defined renamed variable for variables longer than 8 characters
            if len(node.targets[0].id) > 8:
                renamed = "zzz" + str(self.renamedVariableConstant)
                self.renamedVariableConstant += 1
                self.renamedVariables[node.targets[0].id] = renamed
            else:
                self.renamedVariables[node.targets[0].id] = node.targets[0].id

        if any(self.renamedVariables[node.targets[0].id] == i[0] for i in self.results):  # if we've already seen it
            pass 
        else:
            if isinstance(node.value, ast.Constant):
                self.results.add((self.renamedVariables[node.targets[0].id], node.value.value))
            else:
                self.results.add((self.renamedVariables[node.targets[0].id], None))    
            
            
    '''Credit: https://stackoverflow.com/questions/34570992/getting-parent-of-ast-node-in-python'''     
    #  define children and parents of each node in the AST tree upon initialization
    def childParent(self, root_node):
        for node in ast.walk(root_node):
            for child in ast.iter_child_nodes(node):
                child.parent = node
                node.child = child
            

    def visit_FunctionDef(self, node):
        pass
   