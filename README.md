# Py3DepHell
This project presents tools to work with dependencies and provides of python3 projects.

## py3req
This module detects dependencies of python3 packages. It has verbosive **--help** option, but here is simple example how to use it:

## py3prov
This module generate provides for python3 packages. As for **py3req** its **--help** is verbosive enough

## How to
Imagine you have simple project like this one:
```
src/
├── pkg1
│   ├── mod1.py
│   └── subpkg
│       └── mod3.py
└── tests
    └── test1.py
```

Now you want to detect its dependencies:
```
% python3 -m py3dephell.py3req --pip_format src
unittest
re
re
```
Feel free to make it more verbosive:
```
% python3 -m py3dephell.py3req --pip_format --verbose src
py3prov: detected potential module:src
/tmp/.private/kotopesutility/src/tests/test1.py:unittest
/tmp/.private/kotopesutility/src/pkg1/mod1.py:requests os
/tmp/.private/kotopesutility/src/pkg1/subpkg/mod3.py:re
```
As you can see, there are some modules from standart library, so let py3req to learn it:
```
% python3 -m py3dephell.py3req --pip_format --add_prov_path /usr/lib64/python3.11 src
requests
```
That's it! But what if we want to detect its provides, to understand which dependencies it could satisfy? Let's use py3prov!
```
% python3 -m py3dephell.py3prov src
test1
tests.test1
src.tests.test1
mod1
pkg1.mod1
src.pkg1.mod1
mod3
subpkg.mod3
pkg1.subpkg.mod3
src.pkg1.subpkg.mod3
```
Yeah, let's make it more verbosive!
```
% python3 -m py3dephell.py3prov --verbose src/pkg1 src/tests
src/tests:['test1', 'tests.test1', 'src.tests.test1']
src/pkg1:['mod1', 'pkg1.mod1', 'src.pkg1.mod1', 'mod3', 'subpkg.mod3', 'pkg1.subpkg.mod3', 'src.pkg1.subpkg.mod3']
```
