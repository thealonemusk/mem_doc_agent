import os
import tree_sitter_c
from tree_sitter import Language, Parser, Query, QueryCursor

def main():
    c_language = Language(tree_sitter_c.language())
    parser = Parser(c_language)

    allocation_query = Query(c_language, """
    (init_declarator
        declarator: (pointer_declarator
            declarator: (identifier) @var_name)
        value: (cast_expression
            value: (call_expression
                function: (identifier) @func_name
                (#eq? @func_name "pvPortMalloc")
            )
        )
    )
    """)

    queue_send_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        arguments: (argument_list
            (identifier) @queue_name
            (unary_expression
                argument: (identifier) @payload_var)
        )
        (#eq? @func_name "xQueueSend")
    )
    """)

    queue_receive_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        arguments: (argument_list
            (identifier) @queue_name
            (unary_expression
                argument: (identifier) @payload_var)
        )
        (#eq? @func_name "xQueueReceive")
    )
    """)

    free_query = Query(c_language, """
    (call_expression
        function: (identifier) @func_name
        arguments: (argument_list
            (identifier) @freed_var)
        (#eq? @func_name "vPortFree")
    )
    """)

    allocations = {}
    receivers = {}
    freed_vars = []

    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(('.c', '.h')):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    c_code = f.read()
                    tree = parser.parse(c_code)
                    root_node = tree.root_node

                    alloc_cursor = QueryCursor(allocation_query)
                    alloc_captures = alloc_cursor.captures(root_node)
                    if isinstance(alloc_captures, dict) and 'var_name' in alloc_captures:
                        for node in alloc_captures['var_name']:
                            var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                            allocations[var_name] = {"file": file, "line": node.start_point[0] + 1, "status": "active"}
                    elif isinstance(alloc_captures, list):
                        for node, capture_name in alloc_captures:
                            if capture_name == 'var_name':
                                var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                                allocations[var_name] = {"file": file, "line": node.start_point[0] + 1, "status": "active"}

                    send_cursor = QueryCursor(queue_send_query)
                    send_captures = send_cursor.captures(root_node)
                    if isinstance(send_captures, dict) and 'payload_var' in send_captures:
                        for node in send_captures['payload_var']:
                            var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                            if var_name in allocations:
                                allocations[var_name]["status"] = "in_queue"
                    elif isinstance(send_captures, list):
                        for node, capture_name in send_captures:
                            if capture_name == 'payload_var':
                                var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                                if var_name in allocations:
                                    allocations[var_name]["status"] = "in_queue"

                    recv_cursor = QueryCursor(queue_receive_query)
                    recv_captures = recv_cursor.captures(root_node)
                    if isinstance(recv_captures, dict) and 'payload_var' in recv_captures:
                        for node in recv_captures['payload_var']:
                            var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                            receivers[var_name] = {"file": file, "line": node.start_point[0] + 1}
                    elif isinstance(recv_captures, list):
                        for node, capture_name in recv_captures:
                            if capture_name == 'payload_var':
                                var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                                receivers[var_name] = {"file": file, "line": node.start_point[0] + 1}

                    free_cursor = QueryCursor(free_query)
                    free_captures = free_cursor.captures(root_node)
                    if isinstance(free_captures, dict) and 'freed_var' in free_captures:
                        for node in free_captures['freed_var']:
                            var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                            freed_vars.append(var_name)
                    elif isinstance(free_captures, list):
                        for node, capture_name in free_captures:
                            if capture_name == 'freed_var':
                                var_name = c_code[node.start_byte:node.end_byte].decode('utf-8')
                                freed_vars.append(var_name)

    print("--- Memory Doctor Analysis ---")
    for var, info in allocations.items():
        if info["status"] == "active":
            print(f"POTENTIAL LEAK: '{var}' allocated in {info['file']} at line {info['line']} but never freed or passed to queue.")
        elif info["status"] == "in_queue":
            found_free = False
            for rx_var in receivers:
                if rx_var in freed_vars:
                    found_free = True
            
            if found_free:
                print(f"SAFE: '{var}' passed to queue and likely freed by consumer.")
            else:
                print(f"LEAK SUSPECTED: '{var}' passed to queue but no matching free found in consumer.")

if __name__ == "__main__":
    main()