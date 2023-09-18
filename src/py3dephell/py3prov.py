#! /usr/bin/env python3

import os
import re
import sys
import argparse
import sysconfig
from pathlib import Path


so_suffix = sysconfig.get_config_var('EXT_SUFFIX')
shlib_suffix = sysconfig.get_config_var('SHLIB_SUFFIX')
soabi = f'.{sysconfig.get_config_var("SOABI")}{shlib_suffix}'
soabi3 = f'.{sysconfig.get_config_var("SOABI3")}{shlib_suffix}'
abi3 = f'.abi3{shlib_suffix}'


def processing_pth(path):
    '''
    Read new pathes from given file (it should be .pth) and returns new pathes

    :param path: path to the .pth file
    :type path: str or pathlib.Path
    :return: new pathes
    :rtype: list[str]
    '''
    new_names = []
    try:
        with open(path, 'r') as f:
            text = f.readlines()
            for line in text:
                line = line.rstrip()
                if re.match(r'^#|import\s|^$', line):
                    continue
                new_names.append(line)
            path, pth = os.path.split(path)
            new_names = [os.path.join(path, new_dir) for new_dir in new_names]
            return new_names
    except FileNotFoundError:
        print(f'py3prov: No such file or directory:{path}', file=sys.stderr)
        return []


def create_provides_from_path(path, prefixes=sys.path, abs_mode=False,
                              pkg_mode=False, skip_wrong_names=True, skip_namespace_pkgs=True):
    '''
    Creates provides from given path for 1 file.

    :param path: path from which provides will be created
    :type path: str or pathlib.Path
    :param prefixes: list of prefixes by which the path will be trimmed
    :type prefixes: list[str]
    :param abs_mode: create provide only for absolute import (['A.B'] instead of ['B', 'A.B'])
    :type abs_mode: Bool
    :param pkg_mode: create provide even for directory
    :type pkg_mode: Bool
    :param skip_wrong_names: skip provide if they are not an identifier
    :type skip_wrong_names: Bool
    :param skip_namespace_pkgs: do not build provides for namespace packages
    :type skip_namespace_pkgs: Bool
    :return: list of provides created from given path
    :rtype: list[str]
    '''

    if isinstance(path, str):
        path = Path(path)
    elif isinstance(path, Path):
        pass
    else:
        raise TypeError(f'Wrong type:{type(path)} of variable <<path>>, use str or pathlib.Path instead')

    provides = []
    for pref in sorted(prefixes, key=lambda p: (len(p.split('/')), p), reverse=True):
        if pref and (pref := os.path.normpath(pref)) and path.as_posix() != pref\
           and pref in map(lambda x: x.as_posix(), path.parents):
            path = Path(path.as_posix().replace(pref + '/', ''))

    if not path:
        raise ValueError('py3prov.create_provides_from_path: path cannot be empty (possibly it was cut by pref)')

    top_package_flag = False

    trash, *parts = path.parts
    if trash != '/':
        parts.insert(0, trash)

    for suffix in sorted([so_suffix, shlib_suffix, soabi, soabi3, '.py', abi3], key=lambda p: len(p), reverse=True):
        if parts[-1].endswith(suffix):
            parts[-1] = parts[-1].replace(suffix, '', 1)
            module = True
            break
    else:
        module = False

    if module or pkg_mode:
        if parts[-1] == '__init__':
            top_package_flag = True

        if '.' in parts[-1]:
            print(f'py3prov: bad name for provides from path:{path.as_posix()}', file=sys.stderr)

        if abs_mode and (all([part.isidentifier() for part in parts]) or not skip_wrong_names):
            provides.append('.'.join(parts))
        elif not abs_mode:
            while parts:
                if not parts[-1].isidentifier() and skip_wrong_names:
                    break
                if len(provides) > 0:
                    provides.append(f'{parts.pop()}.{provides[-1]}')
                else:
                    provides.append(parts.pop())

    parent = path.parent

    if (top_package_flag or not skip_namespace_pkgs) and parent.as_posix() != '.':
        provides += create_provides_from_path(parent, prefixes,
                                              pkg_mode=True, abs_mode=abs_mode, skip_wrong_names=skip_wrong_names)

    return provides


def search_for_provides(path, prefixes=sys.path, abs_mode=False,
                        skip_wrong_names=True, skip_namespace_pkgs=True):
    '''
    This function walks through given path and search for provides

    :param path: given path
    :type path: str or pathlib.Path
    :param prefixes: list of prefixes by which the path will be trimmed
    :type prefixes: list[str]
    :param abs_mode: create provide only for absolute import (['A.B'] instead of ['B', 'A.B'])
    :type abs_mode: Bool
    :param skip_wrong_names: skip provide if they are not an identifier
    :type skip_wrong_names: Bool
    :param skip_namespace_pkgs: do not build provides for namespace packages
    :type skip_namespace_pkgs: Bool
    :return: list of provides created from given path
    :rtype: list[str]
    '''
    provides = []
    path = Path(path)

    if path.is_file() or path.is_symlink():
        return create_provides_from_path(path.as_posix(), prefixes, abs_mode=abs_mode,
                                         skip_wrong_names=skip_wrong_names, skip_namespace_pkgs=skip_namespace_pkgs)
    elif path.is_dir() and '__pycache__' not in path.as_posix():
        for subpath in path.iterdir():
            provides += search_for_provides(subpath, prefixes, abs_mode, skip_wrong_names, skip_namespace_pkgs)
    return provides


def module_detector(path, prefixes, modules=[], verbose_mode=True):
    '''
    Detect top module according to prefixes

    :param path: path to the potentional module
    :type path: str or pathlib.Path
    :param prefixes: list of prefixes by which the path will be trimmed
    :type prefixes: list[str]
    :param modules: list of already detected modules (usefull with verbose_mode to ignore already detected modules)
    :type modules: list[str]
    :param verbose_mode: turn on verbose mode (print detected modules to the stderr)
    :type verbose_mode: Bool
    :return: pair of detected prefix and top module
    :rtype: (str, str) or (None, None)
    '''
    if isinstance(path, Path):
        path = path.as_posix()
    for pref in sorted(prefixes, key=lambda p: (len(p.split('/')), p), reverse=True):
        if pref and (pref := os.path.normpath(pref)) and path.startswith(pref + '/') and pref != os.path.normpath(path):
            module = re.match(r'%s\/([^\/]+)' % re.escape(pref), path).groups()[0]
            if verbose_mode and module not in modules:
                print(f'py3prov: detected potential module:{module}', file=sys.stderr)
            return pref, module
    return None, None


def pth_detector(pathes, verbose_mode=False):
    '''
    Check if given list of pathes contains working .pth files

    :param pathes: list of pathes
    :type pathes: list[str] or list[pathlib.Path]
    :param verbose_mode: turn on verbose mode
    :type verbose_mode: Bool
    :return: list of new prefixes created by .pth files
    :rtype: list[str]
    '''
    new_prefixes = []
    for path in pathes:
        path = Path(path)
        if not path.exists():
            if verbose_mode:
                print(f'Path {path} does not exist, skip it', file=sys.stderr)
            continue
        if path.suffix == '.pth':
            if verbose_mode:
                print(f'Detected .pth file:{path.absolute().as_posix()}', file=sys.stderr)
            new_prefixes += processing_pth(path.absolute().as_posix())
        elif path.is_dir():
            for item in path.iterdir():
                if item.suffix == '.pth':
                    print(f'Detected .pth file:{item.absolute().as_posix()}', file=sys.stderr)
                    new_prefixes += processing_pth(item.absolute().as_posix())
        else:
            if verbose_mode:
                print(f'Path {path} is not a directory or .pth file, skip it', file=sys.stderr)
    return new_prefixes


def files_filter(files, prefixes=sys.path, only_prefix=False,
                 deep_search=False, verbose_mode=True):
    '''
    Sort files according to the list of prefixes, detect top modules/packages

    :param files: list of files, where provides will be searched for
    :type files: list[str]
    :param prefixes: list of prefixes
    :type prefixes: list[str]
    :only_prefix: create provides only for files with prefix from prefixes
    :type only_prefix: Bool
    :param deep_search: with this option py3prov will try to find all provides according
    to potential module (if it exists). Not fully tested.
    :param verbose_mode: turn on verbose mode
    :type verbose_mode: Bool
    :return: sorted dictionary {file:is_top_module_flag}
    :rtype: {str:str} or {str:None}
    '''

    files_dict = {}

    modules = []
    for file in sorted(files, reverse=True):
        if isinstance(file, Path):
            file = file.as_posix()

        pref, module = module_detector(file, prefixes, modules, verbose_mode)
        if pref and module:
            module_path = re.match(r'%s\/%s(\.py|%s|%s|\/|$)'
                                   % (re.escape(pref), re.escape(module),
                                      re.escape(so_suffix), re.escape(shlib_suffix)), file).group()
            modules.append(module)
            if deep_search:
                for f in files:
                    if f.startswith(module_path):
                        files.remove(f)
                files_dict[module_path] = module
            else:
                files_dict[file] = module

        elif not only_prefix:
            files_dict[file] = None

    return files_dict


def generate_provides(files, prefixes=sys.path, skip_pth=False, only_prefix=False,
                      deep_search=False, abs_mode=False, verbose=True,
                      skip_wrong_names=True, skip_namespace_pkgs=True):
    '''
    Generate provides for given list of files, sorted through prefixes if required, detect top modules.

    :param files: list of files
    :type files: list[str]
    :param prefixes: list of prefixes by which the path will be trimmed
    :type prefixes: list[str]
    :param skip_pth: ignore .pth files
    :type skip_pth: Bool
    :only_prefix: create provides only for files with prefix from prefixes
    :type only_prefix: Bool
    :param deep_search: with this option py3prov will try to find all provides according
    to potential module (if it exists). Not fully tested.
    :param abs_mode: create provide only for absolute import (['A.B'] instead of ['B', 'A.B'])
    :type abs_mode: Bool
    :param verbose: turn on verbose mode
    :param skip_wrong_names: skip provide if they are not an identifier
    :type skip_wrong_names: Bool
    :param skip_namespace_pkgs: do not build provides for namespace packages
    :type skip_namespace_pkgs: Bool
    :return: dict {file:[provides]}
    :rtype: {str:[str]}
    '''
    provides = {}
    files_dict = files_filter(files.copy(), prefixes=prefixes, only_prefix=only_prefix,
                              deep_search=deep_search, verbose_mode=verbose)

    for path, module_name in files_dict.items():
        provides[path] = {'provides': search_for_provides(path, prefixes, abs_mode=abs_mode,
                                                          skip_wrong_names=skip_wrong_names,
                                                          skip_namespace_pkgs=skip_namespace_pkgs),
                          'package': module_name}

    if not skip_pth:
        pth = set()
        for path in files:
            pth |= set(pth_detector(prefixes, verbose))
        prefixes += list(pth)
        new_provides = generate_provides(files, prefixes, True, only_prefix, deep_search, abs_mode, verbose,
                                         skip_wrong_names, skip_namespace_pkgs)
        for key, new_provs in new_provides.items():
            if key in provides:
                if abs_mode:
                    provides[key]['provides'] += [new for new in new_provs['provides']
                                                  if new not in provides[key]['provides']]
                if not provides[key]['package']:
                    provides[key]['package'] = new_provs['package']
            else:
                provides.update({key: new_provs})

    return provides


def main():
    args = argparse.ArgumentParser(description='Search provides for module')
    args.add_argument('--prefixes', help='List of prefixes')
    args.add_argument('--abs_mode', action='store_true',
                      help='Turn on plugin mode (build only absolute provides)')
    args.add_argument('--only_prefix', action='store_true',
                      help='Skip all provides, that are not in prefix')
    args.add_argument('--skip_pth', action='store_true', help='Skip pth files')
    args.add_argument('--verbose', action='store_true', help='Turn on verbose mode')
    args.add_argument('input', nargs='*', default=[],
                      help='List of files from which provides will be created')
    args = args.parse_args()

    if not args.input:
        args.input = sys.stdin.read().split()

    prefixes = args.prefixes.split(',') if args.prefixes else sys.path

    path_provides = generate_provides(files=args.input, prefixes=prefixes,
                                      skip_pth=args.skip_pth, abs_mode=args.abs_mode,
                                      only_prefix=args.only_prefix, verbose=args.verbose)
    for path, provides in path_provides.items():
        if args.verbose:
            print(f'{path}:{[prov for prov in provides["provides"] if isinstance(prov, str)]}')
        else:
            print(*[prov for prov in provides['provides'] if isinstance(prov, str)], sep='\n')


if __name__ == '__main__':
    sys.exit(main())
