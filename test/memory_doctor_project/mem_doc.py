import os
import re
import tree_sitter_c
from tree_sitter import Language, Parser, Query, QueryCursor

def minify_c_code(code_str):
    code_str = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code_str)
    lines = [line for line in code_str.splitlines() if line.strip()]
    return '\n'.join(lines)

def get_enclosing_function(node):
    while node is not None and node.type != 'function_definition':
        node = node.parent
    return node

def get_function_name(func_def_node, source_code):
    decl = func_def_node.child_by_field_name('declarator')
    curr = decl
    while curr is not None:
        if curr.type == 'identifier':
            return source_code[curr.start_byte:curr.end_byte].decode('utf-8')
        next_node = curr.child_by_field_name('declarator')
        if next_node:
            curr = next_node
        else:
            break
    return None

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

    mem_ops_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#match? @func_name "^(SB_malloc|paytm_malloc|SB_free|paytm_free)$")
    )
    """)

    ipc_send_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#match? @func_name "^(xQueueSend|xQueueSendToBack|xQueueSendToFront|osMessagePut)$")
    )
    """)

    ipc_recv_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#match? @func_name "^(xQueueReceive|osEventWait)$")
    )
    """)

    allocators_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        (#match? @func_name "^(SB_malloc|paytm_malloc)$")
    )
    """)

    functions_to_analyze = {}
    discovered_factories = set()
    parsed_files = {}

    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(('.c', '.h')):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    c_code = f.read()
                    tree = parser.parse(c_code)
                    parsed_files[file_path] = (file, c_code, tree)

                    cursor = QueryCursor(mem_ops_query)
                    for match in cursor.matches(tree.root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_node = get_enclosing_function(target_node)
                            if func_node:
                                raw_body = c_code[func_node.start_byte:func_node.end_byte].decode('utf-8')
                                line = func_node.start_point[0] + 1
                                key = f"{file}:{line}"
                                if key not in functions_to_analyze:
                                    functions_to_analyze[key] = {"file": file, "path": file_path, "body": minify_c_code(raw_body), "type": "Direct Memory Op"}

                    cursor = QueryCursor(ipc_send_query)
                    for match in cursor.matches(tree.root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_node = get_enclosing_function(target_node)
                            if func_node:
                                raw_body = c_code[func_node.start_byte:func_node.end_byte].decode('utf-8')
                                line = func_node.start_point[0] + 1
                                key = f"{file}:{line}"
                                if key not in functions_to_analyze:
                                    functions_to_analyze[key] = {"file": file, "path": file_path, "body": minify_c_code(raw_body), "type": "IPC Producer (Queue Send)"}

                    cursor = QueryCursor(ipc_recv_query)
                    for match in cursor.matches(tree.root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_node = get_enclosing_function(target_node)
                            if func_node:
                                raw_body = c_code[func_node.start_byte:func_node.end_byte].decode('utf-8')
                                line = func_node.start_point[0] + 1
                                key = f"{file}:{line}"
                                if key not in functions_to_analyze:
                                    functions_to_analyze[key] = {"file": file, "path": file_path, "body": minify_c_code(raw_body), "type": "IPC Consumer (Queue Receive)"}

                    cursor = QueryCursor(allocators_query)
                    for match in cursor.matches(tree.root_node):
                        target_node = get_node(match[1], 'func_name')
                        if target_node:
                            func_node = get_enclosing_function(target_node)
                            if func_node:
                                func_name = get_function_name(func_node, c_code)
                                if func_name:
                                    discovered_factories.add(func_name)

    if discovered_factories:
        factories_regex = "^(" + "|".join(discovered_factories) + ")$"
        factory_call_query = Query(c_language, f"""
        (call_expression
            function: (identifier) @func_name
            (#match? @func_name "{factories_regex}")
        )
        """)

        for file_path, (file, c_code, tree) in parsed_files.items():
            cursor = QueryCursor(factory_call_query)
            for match in cursor.matches(tree.root_node):
                target_node = get_node(match[1], 'func_name')
                if target_node:
                    func_node = get_enclosing_function(target_node)
                    if func_node:
                        raw_body = c_code[func_node.start_byte:func_node.end_byte].decode('utf-8')
                        line = func_node.start_point[0] + 1
                        key = f"{file}:{line}"
                        if key not in functions_to_analyze:
                            functions_to_analyze[key] = {"file": file, "path": file_path, "body": minify_c_code(raw_body), "type": "Cross-Function Caller"}

    report_content = "# Memory Doctor - Enterprise Cross-Thread Remediation Task\n\n"
    report_content += "### Instructions for AI Agent:\n"
    report_content += "I have extracted the following C functions. They contain memory allocations (`SB_malloc`, `paytm_malloc`), custom factory calls, or Inter-Process Communication (IPC) handoffs.\n\n"
    report_content += "**CRITICAL DIRECTIVES FOR CROSS-THREAD TRACKING:**\n"
    report_content += "1. **Identify the Queue:** Look at the `IPC Producer` functions. Note the name of the queue or mailbox a pointer is sent to.\n"
    report_content += "2. **Bridge the Gap:** Find the corresponding `IPC Consumer` function that reads from that exact same queue name.\n"
    report_content += "3. **Enforce Ownership:** Once the `IPC Consumer` reads the pointer from the queue, it takes ownership. You MUST verify that the Consumer function eventually calls `SB_free` or `paytm_free` on that pointer in all execution paths.\n"
    report_content += "4. If an IPC send fails (e.g., queue is full), ensure the Producer frees the memory before returning.\n"
    report_content += "5. Output the corrected C function for any violations found.\n\n"
    report_content += "---\n\n"

    for key, data in functions_to_analyze.items():
        report_content += f"## Target File: `{data['path']}` | Role: {data['type']}\n"
        report_content += f"```c\n{data['body']}\n```\n\n"

    with open("memory_doctor_report.md", "w") as f:
        f.write(report_content)
    
    print(f"[SUCCESS] -> memory_doctor_report.md generated. Tracking {len(discovered_factories)} custom factories and all IPC endpoints.")

if __name__ == "__main__":
    main()