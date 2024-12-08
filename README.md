# Py3DepHell
This project presents tools to work with dependencies and provides of python3 projects.


## py3prov
This module generate provides for python3 packages. As for **py3req** its **--help** is verbose enough

## py3req
This module detects dependencies of python3 packages. It has verbose **--help** option, but here is simple example how to use it:

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
With the following context:

**src/pkg1/mod1.py**:
```
import re
import sys
import os
import os.path

from .subpkg import mod3
```

**src/pkg1/subpkg/mod3.py**
```
import ast
```

**src/tests/test1.py**
```
import unittest

import pytest
```

### Detecting dependencies
Let's run **py3req** to detect deps for our project:

```
% py3req --verbose src
os.path
re
os
pytest
unittest
ast
```

As you can see, **sys** was not classified as dependency, because **sys** is built-in module, which is provided by interpreter by itself. So such deps are filtered out by **py3req**:

```
% py3req --verbose /tmp/src          
py3req:/tmp/src/pkg1/mod1.py: skipping "sys" lines:[2]
py3req:/tmp/src/pkg1/mod1.py: "tmp.src.pkg1.subpkg" lines:[6] is possibly a self-providing dependency, skip it
/tmp/src/pkg1/mod1.py:os.path re os
/tmp/src/tests/test1.py:pytest unittest
/tmp/src/pkg1/subpkg/mod3.py:ast
```

Moreover, **py3req** recognised dependency from **src/pkg1/mod1.py** to **src/pkg1/subpkg/mod3.py**, but since it is provided by given file list, **py3req** filtered it out.

Now let's exclude dependencies, that are provided by python3 standart library:
```
% py3req --exclude_stdlib src
py3prov: bad name for provides from path:config-3.12-x86_64-linux-gnu
pytest
```

As you can see, **pytest** is the only one founded dependency, that is not provided by python3 standart library. But what if we have dependency, that is provided by our environment or another one package, so we want to exclude it? For such problem we have **--add_prov_path** option:

```
% py3req --exclude_stdlib --add_prov_path src2 src
py3prov: bad name for provides from path:config-3.12-x86_64-linux-gnu
```

Where **src2** has the following structure:
```
src2
└── pytest
    └── __init__.py
```

Another way to exclude such dependency is to ignore it manually, using **--ignore_list** option:
```
% py3req --exclude_stdlib --ignore_list pytest src
py3prov: bad name for provides from path:config-3.12-x86_64-linux-gnu
sys
```
But it makes built-in modules visible.

Finally, there can be deps, that are hidden inside conditions or function calls. For example:

**anime_dld.py**
```
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

```
% py3req anime_dld.py
pytest
os
ast
re
specific_module
```

But it is possible to ignore all deps, that are hidden inside contexts:
```
% py3req --only_external_deps anime_dld.py
os
```

Other options are little bit specific, but there is clear **--help** option output. Please, check it.


### Detecting provides

While dependency is something, that is required (imported) by your project, provides are requirements, that are exported by other projects for yours.

To detect provides for our **src** use **py3prov**:

```
% py3prov src
mod1
pkg1.mod1
src.pkg1.mod1
mod3
subpkg.mod3
pkg1.subpkg.mod3
src.pkg1.subpkg.mod3
test1
tests.test1
src.tests.test1
```

As you can see, some provides are postfixes of others. For example, **pkg1.mod1** is postdfix of **src.pkg1.mod1**. It is useful for situations, when you want to check self-provides. But in general case you need absolute provide from your project, such as **src.pkg1.mod1**, because you can't import something, that is not visible for python3 (what is not prefixed by **sys.path**). So, to exclude strange provides, use **--abs_mode**:

```
% py3prov --abs_mode src
src.pkg1.mod1
src.pkg1.subpkg.mod3
src.tests.test1
```

But all provides are prefixed by **src** or **tests**, while your project should install **pkg1** in user system. To remove such prefixes use **--prefixes** option:
```
% py3prov --abs_mode --prefixes src src
pkg1.mod1
pkg1.subpkg.mod3
tests.test1
```

By default **--prefixes** is set to **sys.path**:
```
% py3prov --abs_mode $TMP/env/lib/python3/site-packages/py3dephell
py3dephell.__init__
py3dephell
py3dephell.py3prov
py3dephell.py3req
```

While **$TMP/env/lib/python3/site-packages/** is included in **sys.path**.


Other options, such as **--only_prefix** and **--skip_pth** are little bit specific, but it is clear, what they can be used for.


# API documentation
For **API** documentation just use **help** command from interpreter or visit this [link](https://altlinux.github.io/py3dephell/).
