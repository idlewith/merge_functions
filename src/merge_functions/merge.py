import argparse
import ast
import inspect

from black import format_str, FileMode


def get_extra_func_source(name, node):
    imported_module = __import__(node.module, fromlist=[name.name])
    imported_function = getattr(imported_module, name.name)
    source_code = inspect.getsource(imported_function)
    return source_code


def is_required_import_statements(keyword, node_fragment):
    if keyword.lower() in node_fragment.lower():
        return False
    return True


def walk_extra_func(tree, keyword):
    extra_func_list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for name in node.names:
                try:
                    if not is_required_import_statements(keyword, node.module):
                        source_code = get_extra_func_source(name, node)
                        extra_func_list.append(source_code + "\n")
                except (ModuleNotFoundError, AttributeError):
                    pass

    return extra_func_list


def get_node_fragment(code_list, node):
    node_fragment_list = code_list[node.lineno - 1 : node.end_lineno]
    return node_fragment_list


def get_required_import_statements(tree, code_list, keywords):
    statements = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            node_fragment_list = get_node_fragment(code_list, node)
            for node_fragment in node_fragment_list:
                bool_list = []
                for keyword in keywords:
                    if is_required_import_statements(keyword, node_fragment):
                        bool_list.append(True)
                    else:
                        bool_list.append(False)

                if all(bool_list):
                    statements.add(node_fragment)

        if isinstance(node, ast.ImportFrom):
            node_fragment_list = get_node_fragment(code_list, node)
            for node_fragment in node_fragment_list:
                bool_list = []
                for keyword in keywords:
                    if is_required_import_statements(keyword, node.module):
                        bool_list.append(True)
                    else:
                        bool_list.append(False)

                if all(bool_list):
                    statements.add(node_fragment)

    return list(statements)


def get_all_import_statements(tree, code_list):
    statements = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            node_fragment = get_node_fragment(code_list, node)
            statements.extend(node_fragment)

    return statements


def get_other_code(code_list, import_statements):
    other = []
    for code in code_list:
        if code not in import_statements:
            other.append(code)
    return other


def get_args():
    desc = "merge functions from other python files."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="main python file, e.g.: main.py",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--modules",
        type=str,
        nargs="+",
        help="modules(or keywords) you want merge functions, e.g.: utils misc",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="output python file, default is one.py, e.g.: one.py",
        required=False,
        default="one.py",
    )

    args = parser.parse_args()
    return args


def merge():
    args = get_args()
    input_file = args.input
    keywords = args.modules
    output_file = args.output

    code = open(input_file).read()
    tree = ast.parse(code)
    code_list = code.splitlines()

    required_import_statements = get_required_import_statements(
        tree,
        code_list,
        keywords,
    )
    multi_module_extra_func_list = []
    for keyword in keywords:
        extra_func_list = walk_extra_func(tree, keyword)
        multi_module_extra_func_list.extend(extra_func_list)

    all_import_statements = get_all_import_statements(tree, code_list)
    other_statements = get_other_code(code_list, all_import_statements)

    new_code_list = (
        required_import_statements
        + multi_module_extra_func_list
        + other_statements
    )
    new_code_str = format_str(
        "\n".join(new_code_list), mode=FileMode(line_length=79)
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_code_str)
