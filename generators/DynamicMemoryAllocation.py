
class DynamicMemoryAllocation():

    def __init__(self, local_vars: dict(), returns) -> None:
        self.__local_vars = local_vars
        self.__memoryAlloc = [x * 2 for x in range(0, len(self.__local_vars))]  # generate intervals of 2 for stack allocation
        self.stackMemory = len(self.__local_vars) * 2  # generate max stack allocation for extraneous variable
        self.returns = returns

    def generate(self):
        print('; Allocating Local (dynamic) memory')
        for count, n in enumerate(self.__local_vars):
            
            varName = n[0]
            # varValue = n[1]
            # stackMemory = self.stackMemory

            print(f'{str(varName+":"):<9}\t.EQUATE {str(self.__memoryAlloc[count])}') # reserving memory
        
        print('; Allocation memory for return variables')
        for returnVar, malloc in self.returns:
            print(f'{str(returnVar+":"):<9}\t.EQUATE {str(malloc)}') # reserving memory


