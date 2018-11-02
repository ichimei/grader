# grader.py (in Python 3)

This program is an automatic grader in Python 3. It builds and runs the
program in subprocesses, and grades it. Compare functions can be
customized to deal with errors between floating point numbers, etc. It
can also run the reference program and generate outputs for given
inputs.

usage: `./grader.py [-h] [-v] [-a] [-b] [-g] [-c C] [-t T] [--version] HW P`

positional arguments:
* `HW`:                  the number of homework
* `P`:                   the number of problem

optional arguments:
* `-h, --help`:          show this help message and exit
* `-v, --verbose`:       show the progress verbosely
* `-a, --all`:           grade all the students listed in `LIST_PATH`
* `-b, --build`:         build the program before grading
* `-g, --generate`:      generate the outputs but not grade
* `-c C, --compiler C`:  specify the compiler, default `gcc`
* `-t T, --timeout T`:   the timeout of subprocesses in seconds, default `1`
* `--version`:           show version and copyright information and exit

Examples:
* Grade problem 1 of homework 2
```
    ./grader.py 2 1
```
* Grade, but show the progress verbosely, and build the program before grading
```
    ./grader.py 2 1 -v -b
    ./grader.py 2 1 -vb      # same as above
```
