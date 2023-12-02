import unittest
from merge_functions.merge import gen_merge_node


class TestMergeNode(unittest.TestCase):
    def test_merge_code(self):
        input_file = "main_demo.py"
        keywords = [
            "demo_module",
            "example_module",
        ]

        expect_merge_code_list = [
            '"""',
            "doc",
            "string",
            '"""',
            "import json",
            "",
            "",
            "def add(a, b):",
            "    return a + b",
            "",
            "",
            "def subtract(a, b):",
            "    return a - b",
            "",
            "",
            "def multiply(a, b):",
            "    return a * b",
            "",
            "",
            "def divide(a, b):",
            "    return a / b if b else 0",
            "",
            "",
            "def return_hello():",
            '    return "hello"',
            "",
            "",
            "def return_bingo():",
            '    return "bingo"',
            "",
            "",
            "def run():",
            "    print(return_hello())",
            "    (a, b) = (3, 4)",
            "    result1 = add(a, b)",
            "    result2 = subtract(a, b)",
            "    result3 = multiply(a, b)",
            "    result4 = divide(a, b)",
            "    result_dict = {",
            '        "result1": result1,',
            '        "result2": result2,',
            '        "result3": result3,',
            '        "result4": result4,',
            "    }",
            "    print(json.dumps(result_dict))",
            "    print(return_bingo())",
            "",
            "",
            'if __name__ == "__main__":',
            "    run()",
            "",
        ]
        expect_merge_code = "\n".join(expect_merge_code_list)

        actual_merge_code = gen_merge_node(
            input_file,
            keywords,
        )
        self.assertEqual(expect_merge_code, actual_merge_code)


if __name__ == "__main__":
    unittest.main()
