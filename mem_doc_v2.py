import os
import tree_sitter_c
from tree_sitter import Language, Parser, Query, QueryCursor

def get_function_body(node, source_code):
    while node is not None and node.type != 'function_definition':
        node = node.parent
    if node is None:
        return None
    return source_code[node.start_byte:node.end_byte].decode('utf-8'), node.start_point[0] + 1

def get_node(captures, key):
    if isinstance(captures, dict) and key in captures:
        return captures[key][0]
    elif isinstance(captures, list):
        for n, name in captures:
            if name == key:
                return n
    return None

def main():
    c_language = Language(tree_sitter_c.language())
    parser = Parser(c_language)

    malloc_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#eq? @func_name "pvPortMalloc")
    )
    """)

    receive_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#eq? @func_name "xQueueReceive")
    )
    """)

    functions_to_analyze = {}

    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(('.c', '.h')):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    c_code = f.read()
                    tree = parser.parse(c_code)
                    root_node = tree.root_node

                    cursor = QueryCursor(malloc_query)
                    for match in cursor.matches(root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_data = get_function_body(target_node, c_code)
                            if func_data:
                                body, line = func_data
                                key = f"{file}:{line}"
                                functions_to_analyze[key] = {"file": file, "type": "Producer/Allocator", "body": body}

                    cursor = QueryCursor(receive_query)
                    for match in cursor.matches(root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_data = get_function_body(target_node, c_code)
                            if func_data:
                                body, line = func_data
                                key = f"{file}:{line}"
                                if key not in functions_to_analyze:
                                    functions_to_analyze[key] = {"file": file, "type": "Consumer/Receiver", "body": body}

    for key, data in functions_to_analyze.items():
        print(f"--- [AI TARGET EXTRACTED] {data['file']} | Type: {data['type']} ---")
        print(data['body'])
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()