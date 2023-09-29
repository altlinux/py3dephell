import pathlib


def prepare_package(path, name, namespace_pkg=False, w_pth=False, level=0):
    level -= 1
    p = pathlib.Path(path)
    pkg = p.joinpath(name)
    pkg.mkdir()
    files_list = []

    if not namespace_pkg:
        files_list += generate_pymodule(pkg, '__init__') if level % 2 else generate_somodule(pkg, '__init__')

    files_list += generate_pymodule(pkg, f'mod_{level if level > 0 else 0}')
    if w_pth:
        pth = p.joinpath(f'{name}.pth')
        pth.write_text(f'{name}\n')
        files_list.append(pth)
    if level > 0:
        files_list += prepare_package(pkg.as_posix(), f'{name}_sub', namespace_pkg, w_pth, level)
    return files_list


def cleanup_package(path):
    p = pathlib.Path(path)
    if p.is_file() or p.is_symlink():
        p.unlink()
    elif p.is_dir():
        for sub in p.iterdir():
            cleanup_package(sub)
        p.rmdir()


def generate_somodule(path, name, byte_code=b'\x7fELF\x02'):
    p = pathlib.Path(path).joinpath(f'{name}.so')
    p.write_bytes(byte_code)
    return [p]


def generate_pymodule(path, name, text=None):
    if text is None:
        text = f'try:\n\tfrom . import {name}_lib\n'
        text += 'except:\n\timport os\n'
        text += 'importlib = __import__("importlib")\n'
        text += 'importlib.import_module("ast")\n'

    p = pathlib.Path(path).joinpath(f'{name}.py')
    p.write_text(text)
    return [p] + generate_somodule(path, f'{name}_lib')
