import os
import re
import tree_sitter_c
import google.generativeai as genai
from tree_sitter import Language, Parser, Query, QueryCursor
from dotenv import load_dotenv

def minify_c_code(code_str):
    code_str = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code_str)
    lines = [line for line in code_str.splitlines() if line.strip()]
    return '\n'.join(lines)

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
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-pro')

    c_language = Language(tree_sitter_c.language())
    parser = Parser(c_language)

    memory_ops_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#match? @func_name "^(pvPortMalloc|vPortFree|malloc|calloc|free|xQueueReceive|xQueueSend)$")
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

                    cursor = QueryCursor(memory_ops_query)
                    for match in cursor.matches(root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_data = get_function_body(target_node, c_code)
                            if func_data:
                                raw_body, line = func_data
                                key = f"{file}:{line}"
                                if key not in functions_to_analyze:
                                    minified_body = minify_c_code(raw_body)
                                    functions_to_analyze[key] = {"file": file, "body": minified_body}

    for key, data in functions_to_analyze.items():
        print(f"\n--- [Memory Doctor AI] Analyzing {data['file']} ---")
        prompt = f"""
        You are an expert embedded C static analyzer. Review this C function.
        Perform a strict Data Flow Analysis on all pointers.
        
        Check for the following critical violations:
        1. MEMORY LEAK: An allocated pointer does not reach a free statement or an RTOS queue send in EVERY execution path.
        2. DANGLING POINTER: A pointer is accessed, read, or written to AFTER it has been passed to a free function or sent to an RTOS queue.
        3. DOUBLE FREE: A pointer is passed to a free function more than once in the same execution path.
        4. ALIAS LEAK: An allocated pointer is assigned to a secondary variable, and the secondary variable escapes or is leaked.

        Code:
        {data['body']}

        Provide your response in this exact format:
        STATUS: [SAFE, LEAK, DANGLING_POINTER, or DOUBLE_FREE]
        TARGET: [The name of the variable at fault]
        REASON: [One sentence explanation]
        FIX: [A brief description of how to fix it, or 'None needed']
        """
        
        try:
            response = model.generate_content(prompt)
            print(response.text.strip())
        except Exception as e:
            print(f"API Error: {e}")

if __name__ == "__main__":
    main()