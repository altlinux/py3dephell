# Py3DepHell
This project presents tools to work with dependencies and provides of python3 projects.

## py3req
This module detects dependencies of python3 packages. It has verbosive **--help** option, but here is simple example how to use it:
```
% python3 -m py3dephell.py3req lib/python3/site-packages/flake8/checker.py                              
python3(__future__)
python3(argparse)
python3(contextlib)
python3(logging)
python3(multiprocessing.pool)
python3(operator)
python3(signal)
python3(tokenize)
python3(typing)
python3(flake8.discover_files)
python3(flake8.options.parse_args)
python3(flake8.plugins.finder)
python3(flake8.style_guide)
```

## py3prov
This module generate provides for python3 packages. As for **py3req** its **--help** is verbosive enough
```
% python3 -m py3dephell.py3prov lib/python3/site-packages/flake8/checker.py
checker
flake8.checker
```
