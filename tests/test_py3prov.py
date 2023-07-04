import sys
import pathlib
import unittest
import tempfile
from shutil import rmtree
from package import prepare_package
from py3dephell import py3prov


# Prepare directory for packages


class TestPy3Prov(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        print(f'Created directory for test:{self.tmp}', file=sys.stderr)
        self.tests_packages = pathlib.Path(self.tmp)

    def test_create_provides_from_path_for_module(self):
        rmtree(self.tmp)
        # Top-module
        test_cases = {0: [{'path': '/sys_path/bad-symbol/module.py', 'prefixes': ['/sys_path/bad-symbol']},
                          ['module']]}

        # Top-module with empty prefixes, but with bad-caracter in path
        test_cases[1] = [{**test_cases[0][0], 'prefixes': []}, ['module']]

        # Top-module with empty prefixes, bad-caracter in path and in abs_mode
        test_cases[2] = [{**test_cases[1][0], 'abs_mode': True}, []]

        # Top-module with empty prefixes with allowed wrong names ("-" and "." in names)
        test_cases[3] = [{**test_cases[1][0], 'skip_wrong_names':False},
                         ['module', 'bad-symbol.module', 'sys_path.bad-symbol.module']]

        # Top-module with empty prefixes with allowed wrong names ("-" and "." in names) in absolute mode
        test_cases[4] = [{**test_cases[3][0], 'abs_mode':True}, ['sys_path.bad-symbol.module']]
        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing create_provides_from_path for module subTest:{subtest_num}"):
                self.assertEqual(py3prov.create_provides_from_path(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

    def test_create_provides_from_path_for_pkg(self):
        rmtree(self.tmp)
        # Module from regular package
        test_cases = {0: [{'path': '/sys_path/bad-symbol/pkg/__init__.py', 'prefixes': ['/sys_path/bad-symbol']},
                          ['__init__', 'pkg.__init__', 'pkg']]}

        # Module from regular package but with strange prefix
        test_cases[1] = [{**test_cases[0][0], 'prefixes': ['/sys_path/bad-symbol/pkg/']}, ['__init__']]

        # Set special flag to indicate that is the package
        test_cases[2] = [{'path': '/sys_path/bad-symbol/pkg/', 'pkg_mode': True}, ['pkg']]

        # Check provides for namespace package
        test_cases[3] = [{'path': '/sys_path/bad-symbol/pkg/mod1.py'}, ['mod1', 'pkg.mod1']]

        # Check provides for namespace package (turned off ingnoring flag)
        test_cases[4] = [{**test_cases[3][0], 'skip_namespace_pkgs': False}, ['mod1', 'pkg.mod1', 'pkg']]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing create_provides_from_path for packages subTest:{subtest_num}"):
                self.assertEqual(py3prov.create_provides_from_path(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

    def test_module_detector(self):
        rmtree(self.tmp)
        # 1 good prefix, 2 bad
        test_cases = {0: [{'path': '/sys_path/pkg/mod1.py',
                           'prefixes': ['/sys_path/', '/', '']},
                          ('/sys_path', 'pkg')]}

        # Same as previos, but without slash in the end of good prefix
        test_cases[1] = [{**test_cases[0][0], 'prefixes': ['/sys_path', '/', '']},
                         ('/sys_path', 'pkg')]

        # All prefixes are bad
        test_cases[2] = [{**test_cases[0][0], 'prefixes': ['/bad_prefix', '/', '']},
                         (None, None)]
        # Same as 1 test, but with pkg in modules list, to check verbosity
        test_cases[3] = [{**test_cases[1][0], 'modules': ['pkg']},
                         ('/sys_path', 'pkg')]

        # Catching top module (without package)
        test_cases[4] = [{**test_cases[1][0], 'path': '/sys_path/mod1.py'},
                         ('/sys_path', 'mod1.py')]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest("Testing module_detector subTest:{subtest_num}"):
                self.assertEqual(py3prov.module_detector(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')
                self.assertEqual(py3prov.module_detector(**inp_out[0], verbose_mode=False), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

    def test_processing_pth(self):
        prepare_package(self.tests_packages, 'pkg_for_pth', w_pth=True, level=1)
        self.assertEqual(py3prov.processing_pth(self.tests_packages.joinpath('pkg_for_pth.pth').as_posix()),
                         [self.tests_packages.joinpath('pkg_for_pth').as_posix()])
        rmtree(self.tmp)

    def test_files_filter(self):
        rmtree(self.tmp)
        non_pref = ['/non_pref/top_mod.py', '/non_pref/pkg', '/non_pref/pkg/mod.py']
        under_pref = ['/libs_pref/top_module.py', '/pkgs_pref/package/',
                      '/pkgs_pref/package/module.py', '/libs_pref/top_pkg']
        test_cases = {}
        # No prefixes and path should be under prefixes, should return empty list
        test_cases[0] = [{'files': non_pref + under_pref, 'prefixes': [], 'only_prefix': True}, {}]

        # Same as previous test but path should not be under prefixes
        test_cases[1] = [{**test_cases[0][0], 'only_prefix': False}, {p: None for p in non_pref + under_pref}]

        # Good prefixes
        test_cases[2] = [{**test_cases[0][0], 'prefixes': ['/libs_pref', '/pkgs_pref/']},
                         {'/libs_pref/top_module.py': 'top_module.py',
                          '/libs_pref/top_pkg': 'top_pkg',
                          '/pkgs_pref/package/': 'package',
                          '/pkgs_pref/package/module.py': 'package'}]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing files_filter subTest:{subtest_num}"):
                self.assertEqual(py3prov.files_filter(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')
                self.assertEqual(py3prov.files_filter(**inp_out[0], verbose_mode=False), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

    def test_search_for_provides(self):
        prepare_package(self.tests_packages, 'pkg_for_searching', w_pth=True, level=1)
        test_cases = {}
        test_cases[0] = [{'path': self.tests_packages.joinpath('pkg_for_searching.pth'), 'find_pth': True}, []]
        test_cases[1] = [{**test_cases[0][0], 'prefixes':[self.tests_packages.as_posix()]},
                         [self.tests_packages.joinpath('pkg_for_searching').as_posix()]]
        test_cases[2] = [{'path': self.tests_packages.joinpath('pkg_for_searching'),
                          'prefixes': [self.tests_packages.as_posix()], 'abs_mode':True},
                         ['pkg_for_searching', 'pkg_for_searching.mod_0',  'pkg_for_searching.mod_0_lib',
                          'pkg_for_searching.__init__']]
        test_cases[3] = [{**test_cases[2][0], 'abs_mode': False},
                         [*test_cases[2][1], 'mod_0', 'mod_0_lib', '__init__']]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing search_for_provides subTest:{subtest_num}"):
                self.assertSetEqual(set(py3prov.search_for_provides(**inp_out[0])), set(inp_out[1]),
                                    msg=f'SubTest:{subtest_num} FAILED')
        rmtree(self.tmp)

    def gen_provs(self, path, forbidden_elems):
        parts = list(pathlib.Path(path).parts)
        parts.reverse()
        provides = []
        for part in parts:
            if set(forbidden_elems) & set(part):
                break
            provides.append(f'{part}.{provides[-1]}' if provides else part)
        return provides

    def test_generate_provides(self):
        prepare_package(self.tests_packages, 'pkg_for_generate_provides', w_pth=True, level=2)

        test_cases = {}
        self.maxDiff = None
        prov_w_init = self.gen_provs(self.tests_packages.joinpath('pkg_for_generate_provides/__init__'),
                                     ['.', '-', '/'])
        prov_wo_init = self.gen_provs(self.tests_packages.joinpath('pkg_for_generate_provides'), ['.', '-', '/'])
        provides = {'provides':  prov_w_init + prov_wo_init, 'package': None}
        test_cases[0] = [{'files': [self.tests_packages.joinpath('pkg_for_generate_provides/__init__.py')],
                          'prefixes': []},
                         {self.tests_packages.joinpath('pkg_for_generate_provides/__init__.py').as_posix(): provides}]
        provides = {'provides': list(filter(lambda x: '.' in x, [prov_w_init, prov_wo_init])),
                    'package': None}
        test_cases[1] = [{**test_cases[0][0], 'abs_mode': True},
                         {self.tests_packages.joinpath('pkg_for_generate_provides/__init__.py').as_posix(): provides}]
        test_cases[2] = [{'files': [self.tests_packages.joinpath('pkg_for_generate_provides')], 'only_prefix':True,
                          'prefixes': []},
                         {}]
        provides = {'provides': ['__init__', 'pkg_for_generate_provides.__init__', 'pkg_for_generate_provides'],
                    'package': 'pkg_for_generate_provides'}
        test_cases[3] = [{**test_cases[0][0], 'prefixes': [self.tests_packages.as_posix()]},
                         {self.tests_packages.joinpath('pkg_for_generate_provides/__init__.py').as_posix(): provides}]
        provides = {'provides': ['pkg_for_generate_provides.__init__', 'pkg_for_generate_provides'],
                    'package': 'pkg_for_generate_provides'}
        test_cases[4] = [{**test_cases[0][0], 'prefixes': [self.tests_packages.as_posix()], 'abs_mode': True},
                         {self.tests_packages.joinpath('pkg_for_generate_provides/__init__.py').as_posix(): provides}]
        provides = {'provides': ['mod_1', 'pkg_for_generate_provides.mod_1'], 'package': 'pkg_for_generate_provides'}
        test_cases[5] = [{'files': [self.tests_packages.joinpath('pkg_for_generate_provides/mod_1.py')],
                          'prefixes': [self.tests_packages.as_posix()]},
                         {self.tests_packages.joinpath('pkg_for_generate_provides/mod_1.py').as_posix(): provides}]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing generate_provides subTest:{subtest_num}"):
                self.assertDictEqual(py3prov.generate_provides(**inp_out[0]), inp_out[1],
                                     msg=f'SubTest:{subtest_num} FAILED')
        rmtree(self.tmp)


if __name__ == '__main__':
    unittest.main()
