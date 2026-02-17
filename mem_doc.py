import os
import re
import tree_sitter_c
from tree_sitter import Language, Parser, Query, QueryCursor

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
                                    functions_to_analyze[key] = {"file": file, "path": file_path, "body": minified_body}

    report_content = "# Memory Doctor - Cursor Remediation Task\n\n"
    report_content += "### Instructions for AI Agent:\n"
    report_content += "I have extracted the following C functions because they contain memory allocations or RTOS queue handoffs. "
    report_content += "Please perform a strict Data Flow Analysis to find memory leaks, dangling pointers, double frees, or alias leaks. "
    report_content += "If you find a violation, directly apply the fix to my codebase.\n\n"
    report_content += "---\n\n"

    for key, data in functions_to_analyze.items():
        report_content += f"## Target File: `{data['path']}`\n"
        report_content += f"```c\n{data['body']}\n```\n\n"

    with open("memory_doctor_report.md", "w") as f:
        f.write(report_content)
    
    print("[SUCCESS] -> memory_doctor_report.md generated without Gemini. Feed this to Cursor!")

if __name__ == "__main__":
    main()