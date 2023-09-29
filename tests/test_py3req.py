import os
import sys
import ast
import pathlib
import tempfile
import unittest
from shutil import rmtree
from package import generate_somodule, generate_pymodule
from py3dephell import py3req


class TestPy3Req(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        print(f'Created directory for test:{self.tmp}', file=sys.stderr)
        self.tests_packages = pathlib.Path(self.tmp)

    def test_is_import_stmt(self):
        rmtree(self.tmp)
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
        rmtree(self.tmp)
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
        rmtree(self.tmp)
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
        rmtree(self.tmp)
        dep_version = os.getenv('RPM_PYTHON3_VERSION', '%s.%s' % sys.version_info[0:2])

        test_cases = {}
        test_cases[0] = [b'\x7fELF\x02', f'python{dep_version}-ABI(64bit)']
        test_cases[1] = [b'\x7fELF\x01', f'python{dep_version}-ABI']
        test_cases[2] = [b'\x7fELF\x03', None]
        test_cases[3] = [b'', None]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.catch_so subTest:{subtest_num}'):
                with open('/dev/null', 'w') as stderr:
                    module = generate_somodule('/tmp', 'module.so', inp_out[0])[0]
                    self.assertEqual(py3req.catch_so(module, stderr), inp_out[1])
        os.unlink(module)

    def test_find_imports_in_ast(self):
        rmtree(self.tmp)
        test_cases = {}
        test_cases[0] = [{'code': '__import__("os")\n__import__("ast")\nfrom . import requests\nfrom os import path\n',
                          'path': '/pkg/module.py', 'Node': None, 'verbose': False, 'skip_subs': False,
                          'prefixes': [], 'only_external_deps': False},
                         ({'os.path': [4]}, {'pkg.requests': [3]}, {'os': [1], 'ast': [2]}, {})]
        test_cases[1] = [{**test_cases[0][0], 'path': '/pkg/subpkg/module.py', 'prefixes': ['/pkg']},
                         ({'os.path': [4]}, {'subpkg.requests': [3]}, {'os': [1], 'ast': [2]}, {})]
        test_cases[2] = [{**test_cases[1][0], 'skip_subs': True},
                         ({'os': [4]}, {'subpkg': [3]}, {'os': [1], 'ast': [2]}, {})]
        test_cases[3] = [{**test_cases[2][0], 'code': 'try:\n\timport os\nexcept:\n\timport sys',
                         'only_external_deps': True},
                         ({}, {}, {}, {'os': [[2]], 'sys': [[[4]]]})]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.find_import_in_ast subTest:{subtest_num}'):
                with open('/dev/null', 'w') as stderr:
                    self.assertTupleEqual(py3req._find_imports_in_ast(**inp_out[0], stderr=stderr), inp_out[1],
                                          msg=f'SubTest:{subtest_num} FAILED')

    def test_filter_requirements(self):
        rmtree(self.tmp)
        pref = f'python{sys.version_info[0]}'

        test_cases = {}
        test_cases[0] = [{'file': None, 'deps': {'os.path': [1], 'sys': [2], 'ast': [3],
                                                 'friend': [4]}, 'skip_flag': True}, []]
        test_cases[1] = [{**test_cases[0][0], 'skip_flag': False},
                         [f'{pref}({mod})' for mod in ['os.path', 'sys', 'ast', 'friend']]]
        test_cases[2] = [{**test_cases[1][0], 'pip_format': True},
                         ['os.path', 'sys', 'ast', 'friend']]
        test_cases[3] = [{**test_cases[2][0], 'ignore_list': ['sys']},
                         ['os.path', 'ast', 'friend']]
        test_cases[4] = [{**test_cases[3][0], 'provides': ['friend']},
                         ['os.path', 'ast']]
        test_cases[5] = [{**test_cases[4][0], 'only_top_module': True},
                         ['os', 'ast']]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.filter_requirements subTest:{subtest_num}'):
                with open('/dev/null', 'w') as stderr:
                    self.assertListEqual(py3req.filter_requirements(**inp_out[0], stderr=stderr), inp_out[1],
                                         msg=f'SubTest:{subtest_num} FAILED')

    def test_generate_requirements(self):
        pref = f'python{sys.version_info[0]}'
        dep_version = os.getenv('RPM_PYTHON3_VERSION', '%s.%s' % sys.version_info[0:2])
        so_dep = f'python{dep_version}-ABI(64bit)'

        module_1 = generate_pymodule(self.tmp, "module_1", text="from . import module_2\nimport os\nimport requests")
        module_2 = generate_pymodule(self.tmp, "module_2", text="import sys\n__import__('unmet')\nimport importlib")
        files = list(map(lambda x: x.absolute().as_posix(), module_1 + module_2))

        test_cases = {}
        test_cases[0] = [{'files': files},
                         list(map(lambda dep: f"{pref}({dep})", ['os', 'requests', 'unmet', 'importlib'])) + [so_dep]]
        test_cases[1] = [{**test_cases[0][0], 'pip_format': True}, ['os', 'requests', 'unmet', 'importlib'] + [so_dep]]
        test_cases[2] = [{**test_cases[0][0], 'exclude_stdlib': True},
                         list(map(lambda dep: f"{pref}({dep})", ['requests', 'unmet'])) + [so_dep]]
        test_cases[3] = [{**test_cases[2][0], 'pip_format': True}, ['requests', 'unmet'] + [so_dep]]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(msg=f'Testing py3req.filter_requirements subTest:{subtest_num}'):
                with open('/dev/null', 'w') as stderr:
                    got = sum(sum(py3req.generate_requirements(**inp_out[0], stderr=stderr).values(),
                                  start=()), start=[])
                    self.assertSetEqual(set(got), set(inp_out[1]),
                                        msg=f'SubTest:{subtest_num} FAILED')
        rmtree(self.tmp)


if __name__ == '__main__':
    unittest.main()
