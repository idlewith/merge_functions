import ast
from merge_functions.exceptions import PythonFileIsEmptyException


class NodeOps:
    def __init__(self, node):
        self.node = node

    def get_func_class(self, name):
        module = __import__(self.node.module, fromlist=[name.name])
        func_class = getattr(module, name.name)
        return func_class

    def is_docstring(self):
        exist = (
            self.node
            and isinstance(self.node, ast.Expr)
            and isinstance(self.node.value, ast.Str)
        )
        return exist

    def is_import_from(self):
        return isinstance(self.node, ast.ImportFrom)

    def is_import(self):
        return isinstance(self.node, ast.Import)

    def is_func(self):
        return isinstance(self.node, ast.FunctionDef)

    def is_class(self):
        return isinstance(self.node, ast.ClassDef)

    def is_func_or_class(self):
        return self.is_func() or self.is_class()

    def is_import_or_import_from(self):
        return self.is_import() or self.is_import_from()

    def is_keywords_in_node_module(self, keywords, is_only_first_module):
        for keyword in keywords:
            if is_only_first_module:
                exist = (
                    f"{keyword.lower()}." in self.node.module.lower()
                    and f".{keyword.lower()}." not in self.node.module.lower()
                )
            else:
                exist = keyword.lower() in self.node.module.lower()

            if exist:
                return exist
        return False


class MultiNodeOps:
    def __init__(self, node_list):
        self.node_list = node_list

    def check_file_content(self):
        """check whether the first node is a document string"""
        if not self.node_list:
            error_text = "python file is empty"
            raise PythonFileIsEmptyException(error_text)

    def has_docstring_node(self):
        first_node = self.node_list[0]
        node_ops = NodeOps(first_node)
        return node_ops.is_docstring()

    def get_last_index(self):
        return len(self.node_list) + 1

    def get_last_import_node_index(self):
        for index, node in enumerate(reversed(self.node_list)):
            node_ops = NodeOps(node)
            if node_ops.is_import_or_import_from():
                last_index = len(self.node_list) - index
                return last_index

        # get empty import node list if no import
        default_index = 0
        return default_index

    def get_node_list_by_range(self, begin, end):
        return self.node_list[begin:end]
