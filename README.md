# Py3DepHell
This project presents tools to work with dependencies and provides of python3 projects.


## py3prov
This module generate provides for python3 packages. As for **py3req** its **--help** is verbose enough

## py3req
This module detects dependencies of python3 packages. It has verbose **--help** option, but here is simple example how to use it:

## How to
[Imagine](https://packaging.python.org/en/latest/tutorials/packaging-projects/) you have simple project like this one:
```shell
├── src
│   └── pkg1
│       ├── mod1.py
│       └── subpkg
│           └── mod3.py
└── tests
    └── test1.py
```
With the following context:

**src/pkg1/mod1.py**:
```python3
import re
import sys
import os
import os.path

import numpy

from .subpkg import mod3
```

**src/pkg1/subpkg/mod3.py**
```python3
import ast
```

**tests/test1.py**
```python3
import unittest

import pytest
```

### Detecting dependencies
Let's run **py3req** to detect deps for our project:

```shell
% py3req src tests
numpy
pytest
```

Let's turn on verbose mode and check what happened with dependencies:
```shell
% py3req --verbose src tests
py3prov: bad name for provides from path:config-3.12-x86_64-linux-gnu
py3req:/tmp/dummy/src/pkg1/mod1.py: "re" lines:[1] is possibly a self-providing dependency, skip it
py3req:/tmp/dummy/src/pkg1/mod1.py: skipping "sys" lines:[2]
py3req:/tmp/dummy/src/pkg1/mod1.py: "os" lines:[3] is possibly a self-providing dependency, skip it
py3req:/tmp/dummy/src/pkg1/mod1.py: "os.path" lines:[4] is possibly a self-providing dependency, skip it
py3req:/tmp/dummy/src/pkg1/mod1.py: "tmp.dummy.src.pkg1.subpkg" lines:[8] is possibly a self-providing dependency, skip it
py3req:/tmp/dummy/src/pkg1/subpkg/mod3.py: "ast" lines:[1] is possibly a self-providing dependency, skip it
py3req:/tmp/dummy/tests/test1.py: "unittest" lines:[1] is possibly a self-providing dependency, skip it
/tmp/dummy/src/pkg1/mod1.py:numpy
/tmp/dummy/tests/test1.py:pytest
```

As you can see, **py3req** recognised dependency from **src/pkg1/mod1.py** to **src/pkg1/subpkg/mod3.py**, but since it is provided by given file list, **py3req** filtered it out.

#### Filtering dependencies

According to the previouse example, **sys** was not classified as a dependency, because **sys** is built-in module, which is provided by interpreter by itself. So such deps are filtered out by **py3req**. To make it visible for **py3req** use option **--include_built-in**:

```shell
% py3req --include_built-in src tests
sys
numpy
pytest
```

Now let's include dependencies, that are provided by python3 standard library:

```shell
% py3req --include_stdlib src tests
re
numpy
os.path
os
ast
pytest
unittest
```

But what if we have dependency, that is provided by our environment or another one package, so we want **py3req** to find it and exclude from dependencies? For such problem we have **--add_prov_path** option:

```shell
% py3req  --add_prov_path src2 src tests
numpy
```

Where **src2** has the following structure:
```shell
src2
└── pytest
    └── __init__.py
```

Another way to exclude such dependency is to ignore it manually, using **--ignore_list** option:
```shell
% py3req --ignore_list pytest src tests
numpy
```

#### Context dependencies

Finally, there can be deps, that are hidden inside conditions or function calls. For example:

**anime_dld.py**
```python3
import os


def func():
    import pytest


try:
    import specific_module
except Exception as ex:
    print(f"I'm sorry, but {ex}")


a = int(input())
if a == 10:
    import ast
else:
    import re
```

In general it is impossible to check if condition **a == 10** is True or False. Moreover it is not clear if **specific_module** is really important for such project or not. So, by default **py3req** catch them all:

```shell
% py3req anime_dld.py
pytest
specific_module
```

But it is possible to ignore all deps, that are hidden inside contexts:
```shell
% py3req --exclude_hidden_deps anime_dld.py
%
```

#### Matching dependencies with environment
Imagine you write your big project, all your dependencies (including building and testing dependencies) are installed to your virtual (or real) environment. So you need to detect your runnning dependencies and match them to packages, installed to your environment, and get **requirements.txt** file, which you can include in your package. For such cases there is **--inspect_env** option:

```shell
% py3req --inspect_env --verbose src
% cat requirements.txt
numpy==2.2.1
```

As you can see, **py3req** saves matched dependencies to **requirements.txt** file.

Now we can get your testing dependencies:
```shell
% py3req --inspect_env --verbose tests
py3prov:INFO: bad name for provides from path:config-3.12-x86_64-linux-gnu
py3prov:INFO: bad name for provides from path:numpy.libs
py3req:/tmp/project/tests/test1.py: "unittest" lines:[1] is possibly a self-providing dependency, skip it
The following deps:pytest was satisfied by package:pytest==8.3.4
% cat requirements.txt
pytest==8.3.4
```

The difference between running **py3req** with option **--inspect_env** and **pip3 freeze** is that the last command lists all packages installed to your environment (including their dependencies). But **py3req** just finds all dependencies of given sources and can match it to the installed packages.

Also there is an extra option for **--inspect_env** which is called **--env_path**. This options lets you to specify path to your environment (where your packages are installed). It is usefull for **CI** or something like that, but by default **py3req** checks your [purelib](https://docs.python.org/3/library/sysconfig.html#installation-paths) and [platlib](https://docs.python.org/3/library/sysconfig.html#installation-paths), so you can skip this option.


Other options are little bit specific, but there is clear **--help** option output. Please, check it.


### Detecting provides

While dependency is something, that is required (imported) by your project, provides are requirements, that are exported by other projects for yours.

To detect provides for our **src** use **py3prov**:

```shell
% py3prov src
src.pkg1.subpkg.mod3
src.pkg1.mod1
```

To get all possible provides (including even modules) use **--full_mode**:

```shell
% py3prov --full_mode src
mod3
subpkg.mod3
pkg1.subpkg.mod3
src.pkg1.subpkg.mod3
mod1
pkg1.mod1
src.pkg1.mod1
```

But all provides are prefixed by **src**, while your project should install **pkg1** in user system. To remove such prefixes use **--prefixes** option:

```shell
% py3prov --prefixes src src
pkg1.subpkg.mod3
pkg1.mod1
```

By default **--prefixes** is set to **sys.path**, while **$TMP/env/lib/python3/site-packages/** is included in **sys.path**.

```shell
% py3prov  $TMP/env/lib/python3/site-packages/py3dephell
py3dephell.__init__
py3dephell
py3dephell.py3prov
py3dephell.py3req
```



Other options, such as **--only_prefix** and **--skip_pth** are little bit specific, but it is clear, what they can be used for. **--only_prefix** exclude those provides, that are not under prefixes. **--skip_pth** ignore [**.pth**](https://docs.python.org/3/library/site.html) files


# API documentation
For **API** documentation just use **help** command from interpreter or visit this [link](https://altlinux.github.io/py3dephell/).
