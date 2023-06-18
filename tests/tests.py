import sys
import pathlib
import unittest

# Bad solution, need to fix it
# I hate myself for that
parent_dir = pathlib.Path(__file__).parent.parent
src_dir = parent_dir.joinpath('src')
sys.path.append(src_dir.as_posix())
import py3prov


def prepare_package(path, name, namespace_pkg=False, w_pth=False, level=0):
    level -= 1
    p = pathlib.Path(path)
    pkg = p.joinpath(name)
    pkg.mkdir()

    if not namespace_pkg:
        init = pkg.joinpath('__init__.py')
        init.write_bytes(b'')

    for i in range(2):
        mod = pkg.joinpath(f'mod_{i}_{level}.py')
        mod.write_bytes(b'')
    if level > 0:
        return prepare_package(pkg.as_posix(), f'{name}_sub', namespace_pkg, w_pth, level)


class TestPy3Prov(unittest.TestCase):
    def test_create_provides_from_path_for_module(self):
        # Top-module
        test_cases = {0: [{'path': '/usr/lib64/python3/site-packages/module.py'}, ['module']]}

        # Top-module with empty prefixes
        test_cases[1] = [{**test_cases[0][0], 'prefixes': []}, ['module']]

        # Top-module with empty prefixes and in abs_mode
        test_cases[2] = [{**test_cases[1][0], 'abs_mode': True}, []]

        # Top-module with empty prefixes with allowed wrong names ("-" and "." in names)
        test_cases[3] = [{**test_cases[1][0], 'skip_wrong_names':False},
                         ['module', 'site-packages.module', 'python3.site-packages.module',
                          'lib64.python3.site-packages.module', 'usr.lib64.python3.site-packages.module']]

        # Top-module with empty prefixes with allowed wrong names ("-" and "." in names) in absolute mode
        test_cases[4] = [{**test_cases[3][0], 'abs_mode':True}, ['usr.lib64.python3.site-packages.module']]
        for subtest_num, inp_out in test_cases.items():
            with self.subTest("Testing create_provides_from_path for module"):
                self.assertEqual(py3prov.create_provides_from_path(**inp_out[0]), inp_out[1])

    def test_create_provides_from_path_for_pkg(self):
        # Module from regular package
        test_cases = {0: [{'path': '/usr/lib64/python3/site-packages/pkg/__init__.py'},
                          ['__init__', 'pkg.__init__', 'pkg']]}

        # Module from regular package but with strange prefix
        test_cases[1] = [{**test_cases[0][0], 'prefixes': ['/usr/lib64/python3/site-packages/pkg/']}, ['__init__']]

        # Set special flag to indicate that is the package
        test_cases[2] = [{'path': '/usr/lib64/python3/site-packages/pkg/', 'pkg_mode': True}, ['pkg']]

        # Check provides for namespace package
        test_cases[3] = [{'path': '/usr/lib64/python3/site-packages/pkg/mod1.py'}, ['mod1', 'pkg.mod1']]

        # Check provides for namespace package (turned off ingnoring flag)
        test_cases[4] = [{**test_cases[3][0], 'skip_namespace_pkgs': False}, ['mod1', 'pkg.mod1', 'pkg']]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest("Testing create_provides_from_path for packages"):
                self.assertEqual(py3prov.create_provides_from_path(**inp_out[0]), inp_out[1])

    def test_module_detector(self):
        test_cases = {0: [{'path': '/usr/lib64/python3/site-packages/pkg/mod1.py',
                           'prefixes': ['/usr/lib64/python3/site-packages/', '/', '']},
                          ('/usr/lib64/python3/site-packages', 'pkg')]}
        test_cases[1] = [{**test_cases[0][0], 'prefixes': ['/usr/lib64/python3/site-packages', '/', '']},
                         ('/usr/lib64/python3/site-packages', 'pkg')]
        test_cases[2] = [{**test_cases[0][0], 'prefixes': ['/usr/lib64/python3/site-package', '/', '']},
                         (None, None)]
        test_cases[3] = [{**test_cases[1][0], 'modules': ['pkg']},
                         ('/usr/lib64/python3/site-packages', 'pkg')]
        test_cases[4] = [{**test_cases[1][0], 'path': '/usr/lib64/python3/site-packages/mod1.py'},
                         ('/usr/lib64/python3/site-packages', 'mod1.py')]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest("Testing module_detector"):
                self.assertEqual(py3prov.module_detector(**inp_out[0]), inp_out[1])
                self.assertEqual(py3prov.module_detector(**inp_out[0], verbose_mode=False), inp_out[1])


if __name__ == '__main__':
    unittest.main()
