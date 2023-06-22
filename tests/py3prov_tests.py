import sys
import pathlib
import unittest
from package import prepare_package, cleanup_package

# Bad solution, need to fix it
# I hate myself for that
parent_dir = pathlib.Path(__file__).parent.parent
src_dir = parent_dir.joinpath('src')
sys.path.append(src_dir.as_posix())
import py3prov


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
            with self.subTest(f"Testing create_provides_from_path for module subTest:{subtest_num}"):
                self.assertEqual(py3prov.create_provides_from_path(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

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
            with self.subTest(f"Testing create_provides_from_path for packages subTest:{subtest_num}"):
                self.assertEqual(py3prov.create_provides_from_path(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

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
            with self.subTest("Testing module_detector subTest:{subtest_num}"):
                self.assertEqual(py3prov.module_detector(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')
                self.assertEqual(py3prov.module_detector(**inp_out[0], verbose_mode=False), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

    def test_processing_pth(self):
        prepare_package('/tmp', 'pkg_for_pth', w_pth=True, level=1)
        self.assertEqual(py3prov.processing_pth('/tmp/pkg_for_pth.pth'), ['/tmp/pkg_for_pth'])
        cleanup_package('/tmp/pkg_for_pth')
        cleanup_package('/tmp/pkg_for_pth.pth')

    def test_files_filter(self):
        non_pref = ['/usr/src/top_mod.py', '/usr/src/pkg', '/usr/src/pkg/mod.py']
        under_pref = ['/usr/lib/top_module.py', '/usr/lib/python3/site-packages/package/',
                      '/usr/lib/python3/site-packages/package/module.py', '/usr/lib/top_pkg']
        test_cases = {}
        test_cases[0] = [{'files': non_pref + under_pref, 'prefixes': [], 'only_prefix': True}, {}]
        test_cases[1] = [{**test_cases[0][0], 'only_prefix': False}, {p: None for p in non_pref + under_pref}]
        test_cases[2] = [{**test_cases[0][0], 'prefixes': ['/usr/lib', '/usr/lib/python3/site-packages/']},
                         {'/usr/lib/top_module.py': 'top_module.py',
                          '/usr/lib/top_pkg': 'top_pkg',
                          '/usr/lib/python3/site-packages/package/': 'package',
                          '/usr/lib/python3/site-packages/package/module.py': 'package'}]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing files_filter subTest:{subtest_num}"):
                self.assertEqual(py3prov.files_filter(**inp_out[0]), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')
                self.assertEqual(py3prov.files_filter(**inp_out[0], verbose_mode=False), inp_out[1],
                                 msg=f'SubTest:{subtest_num} FAILED')

    def test_search_for_provides(self):
        prepare_package('/tmp', 'pkg_for_searching', w_pth=True, level=1)
        test_cases = {}
        test_cases[0] = [{'path': '/tmp/pkg_for_searching.pth', 'find_pth': True}, []]
        test_cases[1] = [{**test_cases[0][0], 'prefixes':['/tmp']}, ['/tmp/pkg_for_searching']]
        test_cases[2] = [{'path': '/tmp/pkg_for_searching', 'prefixes': ['/tmp'], 'abs_mode':True},
                         ['pkg_for_searching', 'pkg_for_searching.mod_0',  'pkg_for_searching.mod_0_lib',
                          'pkg_for_searching.__init__']]
        test_cases[3] = [{**test_cases[2][0], 'abs_mode': False},
                         [*test_cases[2][1], 'mod_0', 'mod_0_lib', '__init__']]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing search_for_provides subTest:{subtest_num}"):
                self.assertSetEqual(set(py3prov.search_for_provides(**inp_out[0])), set(inp_out[1]),
                                    msg=f'SubTest:{subtest_num} FAILED')

        cleanup_package('/tmp/pkg_for_searching')
        cleanup_package('/tmp/pkg_for_searching.pth')

    def test_generate_provides(self):
        prepare_package('/tmp', 'pkg_for_generate_provides', w_pth=True, level=2)

        test_cases = {}
        provides = ['__init__', 'pkg_for_generate_provides.__init__', 'tmp.pkg_for_generate_provides.__init__',
                    'pkg_for_generate_provides', 'tmp.pkg_for_generate_provides', None]
        test_cases[0] = [{'files': ['/tmp/pkg_for_generate_provides/__init__.py'], 'prefixes': []},
                         {'/tmp/pkg_for_generate_provides/__init__.py': provides}]
        provides = ['tmp.pkg_for_generate_provides.__init__', 'tmp.pkg_for_generate_provides', None]
        test_cases[1] = [{**test_cases[0][0], 'abs_mode': True},
                         {'/tmp/pkg_for_generate_provides/__init__.py': provides}]
        test_cases[2] = [{'files': ['/tmp/pkg_for_generate_provides'], 'only_prefix':True, 'prefixes': []}, {}]
        provides = ['__init__', 'pkg_for_generate_provides.__init__', 'pkg_for_generate_provides',
                    'pkg_for_generate_provides']
        test_cases[3] = [{**test_cases[0][0], 'prefixes': ['/tmp']},
                         {'/tmp/pkg_for_generate_provides/__init__.py': provides}]
        provides = ['pkg_for_generate_provides.__init__', 'pkg_for_generate_provides', 'pkg_for_generate_provides']
        test_cases[4] = [{**test_cases[0][0], 'prefixes': ['/tmp'], 'abs_mode': True},
                         {'/tmp/pkg_for_generate_provides/__init__.py': provides}]
        provides = ['mod_1', 'pkg_for_generate_provides.mod_1', 'pkg_for_generate_provides']
        test_cases[5] = [{'files': ['/tmp/pkg_for_generate_provides/mod_1.py'], 'prefixes': ['/tmp']},
                         {'/tmp/pkg_for_generate_provides/mod_1.py': provides}]

        for subtest_num, inp_out in test_cases.items():
            with self.subTest(f"Testing generate_provides subTest:{subtest_num}"):
                self.assertDictEqual(py3prov.generate_provides(**inp_out[0]), inp_out[1],
                                     msg=f'SubTest:{subtest_num} FAILED')

        cleanup_package('/tmp/pkg_for_generate_provides')
        cleanup_package('/tmp/pkg_for_generate_provides.pth')


if __name__ == '__main__':
    unittest.main()
