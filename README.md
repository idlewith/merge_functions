# Merge functions from other python files

this is a dirty way to merge functions from other python files into one python file in order to deploy fast.


## install merge_functions


using python 3.9

```
pip install merge_functions
pip install astunparse=1.6.3
```

## how to use

if you want to import from current directory python file, you need set environment:

if you current path is: `~/code` or `D:\code`

mac or linux: 

```
export PYTHONPATH=~/code
```

windows

```
set PYTHONPATH=D:\code
```

help info

```
mf -h
```

simple example: 

```
mf -i main.py -m demo
```

this will import need functions and classes


```
mf -i main.py -m demo -a
```

- -i: input file
- -m: modules or keywords in modules
- -a: get all code from source file

**then, demo's functions will merge into `one.py`**

PS: the code you need merge from extra module must in from ... import ... statements

`main.py` below

```python
from demo import add, subtract, multiply, divide
import json


def run():
    a, b = 3, 4
    result1 = add(a, b)
    result2 = subtract(a, b)
    result3 = multiply(a, b)
    result4 = divide(a, b)
    result_dict = {
        "result1": result1,
        "result2": result2,
        "result3": result3,
        "result4": result4,
    }
    print(json.dumps(result_dict))


if __name__ == "__main__":
    run()

```

`demo.py` below

```python
def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    return a / b if b else 0

```

## Pycharm settings


External tools settings

Program

```
$PyInterpreterDirectory$/mf.exe
```

Arguments

```
-i $FilePath$ -m utils -a
```

Working directory

```
$ProjectFileDir$
```

Advanced Options

```
Synchronize files after exection
Open console for tool output
```



