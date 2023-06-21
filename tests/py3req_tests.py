import sys
import ast
import unittest
import pathlib

# Bad solution, need to fix it
# I hate myself for that
parent_dir = pathlib.Path(__file__).parent.parent
src_dir = parent_dir.joinpath('src')
sys.path.append(src_dir.as_posix())
import py3req


class TestPy3Req(unittest.TestCase):
    def test_is_import_stmt(self):
        test_cases = {}
        test_cases[0] = ['__import__("os")', [None, 'os']]
        test_cases[1] = ['os = __import__("os")', [None, 'os']]
        test_cases[2] = ['os = __import__("%s" % "os")', [None]]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.is_import_stmt subTest:{subtest_num}'):
                outputs = map(lambda out: out.value if out else None,
                              [py3req.is_import_stmt(n) for n in ast.walk(ast.parse(inp_out[0]))])
                self.assertSetEqual(set(outputs), set(inp_out[1]), msg=f'SubTest:{subtest_num} FAILED')

    def test_is_importlib_call(self):
        test_cases = {}
        test_cases[0] = ['importlib.import_module("os")', [None, 'os']]
        test_cases[1] = ['os = importlib.import_module("os")', [None, 'os']]
        test_cases[2] = ['os = importlib.import_module("%s" % "os")', [None]]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.is_importlib_call subTest:{subtest_num}'):
                outputs = map(lambda out: out.value if out else None,
                              [py3req.is_importlib_call(n) for n in ast.walk(ast.parse(inp_out[0]))])
                self.assertSetEqual(set(outputs), set(inp_out[1]), msg=f'SubTest:{subtest_num} FAILED')


if __name__ == '__main__':
    unittest.main()
