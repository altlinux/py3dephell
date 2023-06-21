import os
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


def generate_somodule(path, name, byte_code):
    p = pathlib.Path(path).joinpath(f'{name}.so')
    p.write_bytes(byte_code)
    return [p]


def generate_pymodule(path, name):
    text = f'try:\n\tfrom . import {name}_friend\n'
    text += 'except:\n\timport os\n'
    text += 'importlib = __import__("importlib")\n'
    text += 'importlib.import_module("ast")\n'

    p = pathlib.Path(path).joinpath(f'{name}.py')
    p.write_text(text)
    return [p] + generate_somodule(path, f'{name}_friend', b'\x7fELF\x02')


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

    def test_build_full_qualified_name(self):
        test_cases = {}
        test_cases[0] = [{'path': 'pkg1/pkg2/pkg3', 'level': 1},
                         pathlib.Path('pkg1/pkg2').absolute().as_posix().replace('/', '.')[1:]]
        test_cases[1] = [{**test_cases[0][0], 'level': 2},
                         pathlib.Path('pkg1').absolute().as_posix().replace('/', '.')[1:]]
        test_cases[2] = [{**test_cases[0][0], 'dependency': 'rabbit'},
                         pathlib.Path('pkg1/pkg2/rabbit').absolute().as_posix().replace('/', '.')[1:]]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.build_full_qualified_name subTest:{subtest_num}'):
                self.assertEqual(py3req.build_full_qualified_name(**inp_out[0]), inp_out[1])

    def test_catch_so(self):
        dep_version = os.getenv('RPM_PYTHON3_VERSION', '%s.%s' % sys.version_info[0:2])

        test_cases = {}
        test_cases[0] = [b'\x7fELF\x02', f'python{dep_version}-ABI(64bit)']
        test_cases[1] = [b'\x7fELF\x01', f'python{dep_version}-ABI']
        test_cases[2] = [b'\x7fELF\x03', None]
        test_cases[3] = [b'', None]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.catch_so subTest:{subtest_num}'):
                with open('/dev/stderr', 'w') as stderr:
                    module = generate_somodule('/tmp', 'module.so', inp_out[0])[0]
                    self.assertEqual(py3req.catch_so(module, stderr), inp_out[1])
        os.unlink(module)

    def test_find_imports_in_ast(self):
        test_cases = {}
        test_cases[0] = [{'code': '__import__("os")\n__import__("ast")\nfrom . import requests\nfrom os import path\n',
                          'path': '/pkg/module.py', 'Node': None, 'verbose': False, 'skip_subs': False,
                          'prefix': [], 'only_external_deps': False},
                         ({'os.path': [4]}, {'pkg.requests': [3]}, {'os': [1], 'ast': [2]}, {})]
        test_cases[1] = [{**test_cases[0][0], 'path': '/pkg/subpkg/module.py', 'prefix':['/pkg']},
                         ({'os.path': [4]}, {'subpkg.requests': [3]}, {'os': [1], 'ast': [2]}, {})]
        test_cases[2] = [{**test_cases[1][0], 'skip_subs': True},
                         ({'os': [4]}, {'subpkg': [3]}, {'os': [1], 'ast': [2]}, {})]
        test_cases[3] = [{**test_cases[2][0], 'code': 'try:\n\timport os\nexcept:\n\timport sys',
                         'only_external_deps': True},
                         ({}, {}, {}, {'os': [[2]], 'sys': [[[4]]]})]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.find_import_in_ast subTest:{subtest_num}'):
                with open('/dev/null', 'r') as stderr:
                    self.assertTupleEqual(py3req._find_imports_in_ast(**inp_out[0], stderr=stderr), inp_out[1],
                                          msg=f'SubTest:{subtest_num} FAILED')


if __name__ == '__main__':
    unittest.main()
