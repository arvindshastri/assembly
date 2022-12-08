import argparse
import ast
from visitors.BottomLevelProgram import BottomLevelProgram

from visitors.GlobalVariables import GlobalVariableExtraction
from visitors.TopLevelProgram import TopLevelProgram
from visitors.LocalVariables import LocalVariableExtraction
from generators.StaticMemoryAllocation import StaticMemoryAllocation
from generators.EntryPoint import EntryPoint
from generators.DynamicMemoryAllocation import DynamicMemoryAllocation

def main():
    input_file, print_ast = process_cli()
    with open(input_file) as f:
        source = f.read()
    node = ast.parse(source)
    if print_ast:
        print(ast.dump(node, indent=2))
    else:
        process(input_file, node)
    
def process_cli():
    """"Process Command Line Interface options"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='filename to compile (.py)')
    parser.add_argument('--ast-only', default=False, action='store_true')
    args = vars(parser.parse_args())
    return args['f'], args['ast_only']

def process(input_file, root_node):
    
    print(f'; Translating {input_file}')
    globalExtractor = GlobalVariableExtraction(root_node)
    globalExtractor.visit(root_node)

    localExtractor = LocalVariableExtraction(root_node, globalExtractor.renamedVariables)
    localExtractor.visit(root_node)

    global_memory_alloc = StaticMemoryAllocation(globalExtractor.results)
    local_memory_alloc = DynamicMemoryAllocation(localExtractor.results, localExtractor.returns)

    print('; Branching to top level (tl) instructions')
    print('\t\tBR tl')

    global_memory_alloc.generate()
    local_memory_alloc.generate()

    top_level = TopLevelProgram('tl', globalExtractor.renamedVariables, localExtractor.renamedVariables, localExtractor.returns, local_memory_alloc.stackMemory)
    top_level.visit(root_node)

    ep = EntryPoint(top_level.finalize())
    ep.generate() 


if __name__ == '__main__':
    main()
