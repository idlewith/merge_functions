import argparse
import ast
import inspect

import isort
from black import format_str, FileMode

from merge_functions.exceptions import (
    NotPythonFileException,
    PythonFileIsEmptyException,
)


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


def is_import_node(node):
    is_import = isinstance(node, ast.Import) or isinstance(
        node, ast.ImportFrom
    )
    if is_import:
        return True

    return False


def get_last_import_node_index(node_list):
    for index, node in enumerate(reversed(node_list)):
        if is_import_node(node):
            last_index = len(node_list) - index
            return last_index

    # get empty import node list if no import
    default_index = 0
    return default_index


def get_keyword_import_node_list(node_list, keywords):
    keyword_node_list = []
    for node in node_list:
        if not isinstance(node, ast.ImportFrom):
            continue

        is_keyword = judge_keywords_in_module_name(keywords, node.module)
        if not is_keyword:
            continue

        keyword_node_list.append(node)

    return keyword_node_list


def get_rest_import_node_list(node_list, keywords):
    rest_node_list = []
    for node in node_list:
        if not isinstance(node, ast.ImportFrom):
            rest_node_list.append(node)
            continue

        is_keyword = judge_keywords_in_module_name(keywords, node.module)
        if is_keyword:
            continue

        rest_node_list.append(node)

    return rest_node_list


def judge_keywords_in_module_name(keywords, module_name):
    """any single keyword in module name"""
    for keyword in keywords:
        is_keyword = keyword.lower() in module_name.lower()
        if is_keyword:
            return True

    return False


def parse_tree_from_file(filename):
    with open(filename, encoding="utf-8") as f:
        tree = ast.parse(f.read())
        return tree


def get_extra_files_import_node_list(node_list):
    import_node_list = []
    for node in node_list:
        for name in node.names:
            module = __import__(node.module, fromlist=[name.name])
            func_class = getattr(module, name.name)

            source_file = inspect.getsourcefile(func_class)
            tree = parse_tree_from_file(source_file)

            for node_extra in tree.body:
                if not is_import_node(node_extra):
                    continue

                import_node_list.append(node_extra)

    return import_node_list


def gen_extra_files_func_class_node_list(node_list):
    func_class_node_list = []
    for node in node_list:
        for name in node.names:
            module = __import__(node.module, fromlist=[name.name])
            func_class = getattr(module, name.name)
            source_code = inspect.getsource(func_class)
            tree = ast.parse(source_code)
            if not tree.body:
                continue

            func_class_node = tree.body[0]
            func_class_node_list.append(func_class_node)

    return func_class_node_list


def check_file_type(filename, file_type=".py"):
    is_python_file = filename.lower().endswith(file_type)
    if not is_python_file:
        error_text = "input file is not python file"
        raise NotPythonFileException(error_text)


def check_file_content(node_list):
    """check whether the first node is a document string"""
    if not node_list:
        error_text = "python file is empty"
        raise PythonFileIsEmptyException(error_text)


def gen_merge_node(input_file, keywords):
    check_file_type(input_file)

    tree = parse_tree_from_file(input_file)
    node_list = tree.body

    check_file_content(node_list)

    is_docstr_node_exist = judge_docstr_node_exist(node_list)
    start_index_for_import = gen_start_index_for_import(is_docstr_node_exist)
    last_index_for_import = get_last_import_node_index(node_list)
    import_node_list = node_list[start_index_for_import:last_index_for_import]
    rest_node_list = node_list[last_index_for_import : len(node_list) + 1]

    # fileter extra modules
    rest_import_node_list = get_rest_import_node_list(
        import_node_list,
        keywords,
    )
    # get import node from extra module files
    keyword_import_node_list = get_keyword_import_node_list(
        import_node_list,
        keywords,
    )

    # generate the node list of extra modules
    extra_files_func_class_node_list = gen_extra_files_func_class_node_list(
        keyword_import_node_list,
    )
    # generate the import node list of extra modules
    extra_files_import_node_list = get_extra_files_import_node_list(
        keyword_import_node_list,
    )

    normal_node_list = (
        rest_import_node_list
        + extra_files_import_node_list
        + extra_files_func_class_node_list
        + rest_node_list
    )
    if is_docstr_node_exist:
        first_doc_node = node_list[0]
        tree.body = [first_doc_node] + normal_node_list
    else:
        tree.body = normal_node_list

    # convert the modified syntax tree to python code
    new_code = ast.unparse(tree)
    # sort import
    new_code = isort.code(new_code)
    # format code
    new_code = format_str(new_code, mode=FileMode(line_length=79))

    return new_code


def gen_start_index_for_import(is_docstring_node_exist):
    start_index = 0
    if is_docstring_node_exist:
        start_index = 1

    return start_index


def judge_docstr_node_exist(node_list):
    first_node = node_list[0]
    is_docstring_node_exist = (
        node_list
        and isinstance(first_node, ast.Expr)
        and isinstance(first_node.value, ast.Str)
    )
    return is_docstring_node_exist


def merge():
    args = get_args()
    input_file = args.input
    keywords = args.modules
    output_file = args.output

    merge_node = gen_merge_node(input_file, keywords)

    # write code to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merge_node)
