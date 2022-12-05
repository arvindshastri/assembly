
class StaticMemoryAllocation():

    def __init__(self, global_vars: dict()) -> None:
        self.__global_vars = global_vars

    def generate(self):
        print('; Allocating Global (static) memory')
        for n in self.__global_vars:
            ## anything that's not a constant is BLOCK 2, _CAPITAL is EQUATE n, constant is WORD n
            varName = n[0]
            varValue = n[1]

            if varValue is not None:
                if varName[0] == "_" and varName[1:].isupper():
                    print(f'{str(varName+":"):<9}\t.EQUATE {str(varValue)}') # reserving memory
                else:
                    print(f'{str(varName+":"):<9}\t.WORD {str(varValue)}') # reserving memory
            else:
                print(f'{str(varName+":"):<9}\t.BLOCK 2') # reserving memory
