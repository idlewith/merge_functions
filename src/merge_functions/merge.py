import argparse
import ast
import inspect

import isort
from black import format_str, FileMode

from merge_functions.exceptions import NotPythonFileException
from merge_functions.node import NodeOps, MultiNodeOps


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
    parser.add_argument(
        "-a",
        "--get_all_code",
        action="store_true",
        help=(
            "once pass this argument, "
            "get all functions and classes to one file"
        ),
        required=False,
    )

    args = parser.parse_args()
    return args


class MainNode:
    def __init__(self, keywords, multi_node_ops: MultiNodeOps):
        self.keywords = keywords
        self.multi_node_ops = multi_node_ops

    def get_import_node_list(self):
        begin = 0
        if self.multi_node_ops.has_docstring_node():
            begin = 1

        end = self.multi_node_ops.get_last_import_node_index()
        return self.multi_node_ops.get_node_list_by_range(begin, end)

    def get_rest_import_node_list(self):
        node_list = self.get_import_node_list()
        rest_import_node_list = []
        for node in node_list:
            node_ops = NodeOps(node)
            if not node_ops.is_import_from():
                rest_import_node_list.append(node)
                continue

            if node_ops.is_keywords_in_node_module(self.keywords):
                continue

            rest_import_node_list.append(node)

        return rest_import_node_list

    def get_keyword_import_node_list(self):
        node_list = self.get_import_node_list()
        keyword_node_list = []
        for node in node_list:
            node_ops = NodeOps(node)
            if not node_ops.is_import_from():
                continue

            if not node_ops.is_keywords_in_node_module(self.keywords):
                continue

            keyword_node_list.append(node)

        return keyword_node_list

    def get_rest_node_list(self):
        begin = self.multi_node_ops.get_last_import_node_index()
        end = self.multi_node_ops.get_last_index()
        return self.multi_node_ops.get_node_list_by_range(begin, end)


class ExtraNode:
    def __init__(self, multi_node_ops, is_get_all_code):
        self.multi_node_ops = multi_node_ops
        self.is_get_all_code = is_get_all_code

    @staticmethod
    def is_import_condition(node):
        node_ops = NodeOps(node)
        return node_ops.is_import_or_import_from()

    @staticmethod
    def is_func_or_class_condition(node):
        node_ops = NodeOps(node)
        return node_ops.is_func_or_class()

    def get_all_func_class_node_list(self):
        return self.get_filtered_node_list(self.is_func_or_class_condition)

    def get_func_class_node_list_by_keyword(self):
        node_list = self.multi_node_ops.node_list
        func_class_node_list = []
        for node in node_list:
            node_ops = NodeOps(node)
            for name in node.names:
                func_class = node_ops.get_func_class(name)
                source_code = inspect.getsource(func_class)
                node_list = ast.parse(source_code).body
                if not node_list:
                    continue

                func_class_node = node_list[0]
                func_class_node_list.append(func_class_node)

        return func_class_node_list

    def get_func_class_node_list(self):
        if self.is_get_all_code:
            return self.get_all_func_class_node_list()
        else:
            return self.get_func_class_node_list_by_keyword()

    def get_filtered_node_list(self, condition_func):
        node_list = self.multi_node_ops.node_list
        filtered_node_list = []
        for node in node_list:
            node_ops = NodeOps(node)
            for name in node.names:
                func_class = node_ops.get_func_class(name)
                source_file = inspect.getsourcefile(func_class)
                extra_node_list = parse_tree_body_from_file(source_file)

                filtered_nodes = filter(condition_func, extra_node_list)
                filtered_node_list.extend(filtered_nodes)

        return filtered_node_list

    def get_import_node_list(self):
        return self.get_filtered_node_list(self.is_import_condition)


def check_file_type(filename, file_type=".py"):
    is_python_file = filename.lower().endswith(file_type)
    if not is_python_file:
        error_text = "input file is not python file"
        raise NotPythonFileException(error_text)


def parse_tree_body_from_file(filename):
    with open(filename, encoding="utf-8") as f:
        tree = ast.parse(f.read())
        return tree.body


def gen_tree():
    tree = ast.Module()
    tree.type_ignores = []
    return tree


def gen_merge_node(input_file, args):
    check_file_type(input_file)
    node_list = parse_tree_body_from_file(input_file)

    full_multi_node_ops = MultiNodeOps(node_list)
    full_multi_node_ops.check_file_content()
    is_docstr_node_exist = full_multi_node_ops.has_docstring_node()

    main_node = MainNode(args.modules, full_multi_node_ops)
    rest_import_node_list = main_node.get_rest_import_node_list()
    keyword_import_node_list = main_node.get_keyword_import_node_list()
    rest_node_list = main_node.get_rest_node_list()

    keyword_multi_node_ops = MultiNodeOps(keyword_import_node_list)
    extra_node = ExtraNode(keyword_multi_node_ops, args.get_all_code)
    extra_files_func_class_node_list = extra_node.get_func_class_node_list()
    extra_files_import_node_list = extra_node.get_import_node_list()

    normal_node_list = (
        rest_import_node_list
        + extra_files_import_node_list
        + extra_files_func_class_node_list
        + rest_node_list
    )
    tree = gen_tree()
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


def merge():
    args = get_args()
    input_file = args.input
    output_file = args.output

    merge_node = gen_merge_node(input_file, args)

    # write code to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(merge_node)
