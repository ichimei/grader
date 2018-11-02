#!/usr/bin/env python3

'''

grader.py (in Python 3): The automatic grader.
Copyright (C) 2018  Yifan Cao

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Description:

This program is an automatic grader in Python 3. It builds and runs the
program in subprocesses, and grades it. Compare functions can be
customized to deal with errors between floating point numbers, etc. It
can also run the reference program and generate outputs for given
inputs.

usage: ./grader.py [-h] [-v] [-a] [-b] [-g] [-c C] [-t T] [--version] HW P

The automatic grader in Python 3.

positional arguments:
  HW                  the number of homework
  P                   the number of problem

optional arguments:
  -h, --help          show this help message and exit
  -v, --verbose       show the progress verbosely
  -a, --all           grade all the students listed in LIST_PATH
  -b, --build         build the program before grading
  -g, --generate      generate the outputs but not grade
  -c C, --compiler C  specify the compiler, default 'gcc'
  -t T, --timeout T   the timeout of subprocesses in seconds, default 1
  --version           show version and copyright information and exit

Examples:
    ./grader.py 2 1          # grade problem 1 of homework 2
    ./grader.py 2 1 -v -b    # grade, but show the progress verbosely,
                             # and build the program before grading
    ./grader.py 2 1 -vb      # same as above

'''

import sys, argparse, subprocess, re

PROGNAME = 'grader.py (in Python 3)'
VERSION = '1.0'
YEAR = '2018'
AUTHOR = 'Yifan Cao'
DESC = 'The automatic grader in Python 3.'

COPYLEFT = '''
{} {}
Copyright (C) {}  {}

License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
'''.format(PROGNAME, VERSION, YEAR, AUTHOR)

USEARGS = True     # Use the arguments passed instead of values below
VERBOSE = True     # Print the details of each testcase or not
ALL = False        # Grade all the students in LIST_PATH or not
BUILD = False      # Build or not (before grading)
GENERATE = False   # Generate the outputs instead of grading or not
COMPILER = 'gcc'   # builder / compiler
COMPILER_OPTION = []    # more options for the builder
TIMEOUT = 1   # the timeout of the subprocess (in seconds)

FILE_IN_STYLE = 'test_hw{}/p{}/{}.in'      # Testcases input path
FILE_OUT_STYLE = 'test_hw{}/p{}/{}.out'    # Testcases output path
REF_SRC_STYLE = './hw{}_{}.c'    # Source file path for a reference program
REF_EXEC_STYLE = './hw{}_{}'     # Executable path for a reference program
STU_SRC_STYLE = './hw{}_{}.c'    # Source file path for a single student's program
STU_EXEC_STYLE = './hw{}_{}'     # Executable path for a single student's program
ALL_STU_SRC_STYLE = 'gitlab/{0}/hw{1}/hw{1}_{2}.c'    # Source file path for all students' program
ALL_STU_EXEC_STYLE = 'gitlab/{0}/hw{1}/hw{1}_{2}'     # Executable path for all students' program
FILE_LIST = './list.txt'    # File of the students list

'''
The homework map. Stores configurations of every problem of every
homework. A configuration is a 2-tuple: The number of testcases, and the
customized compare function (use 'default_compare' for the default one)
'''

HW_MAP = {
    '2': {
        '1': (10, 'match_level_compare'),
        '2': (10, 'match_level_compare'),
        '3': (10, 'match_level_compare_p3'),
    },
}

RED = '\033[1;31m'
PURPLE = '\033[1;35m'
BOLD = '\033[;1m'
RESET = '\033[0;0m'
PROG = sys.argv[0]

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        sys.stderr.write('\n{}{}: {}error: {}{}\n'.format(BOLD, PROG, RED, RESET, message))
        sys.exit(2)

    def warning(self, message):
        sys.stderr.write('{}{}: {}warning: {}{}\n\n'.format(BOLD, PROG, PURPLE, RESET, message))

def get_args():
    parser = Parser(prog=PROG, description=DESC, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('hw', metavar='HW', type=str, help='the number of homework')
    parser.add_argument('p', metavar='P', type=str, help='the number of problem')
    parser.add_argument('-v', '--verbose', help='show the progress verbosely', action='store_true')
    parser.add_argument('-a', '--all', help='grade all the students listed in LIST_PATH', action='store_true')
    parser.add_argument('-b', '--build', help='build the program before grading', action='store_true')
    parser.add_argument('-g', '--generate', help='generate the outputs but not grade', action='store_true')
    parser.add_argument('-c', '--compiler', metavar='C', help='specify the compiler, default \'%(default)s\'', type=str, default='gcc')
    parser.add_argument('-t', '--timeout', metavar='T', help='the timeout of subprocesses in seconds, default %(default)s', type=float, default=1)
    parser.add_argument('--version', help='show version and copyright information and exit', action='version', version = COPYLEFT)
    args = parser.parse_args()

    if not USEARGS:
        return args.hw, args.p

    if not 0 <= args.timeout < float('inf'):
        parser.error('timeout value must be positive')
    if args.hw not in HW_MAP or args.p not in HW_MAP[args.hw]:
        parser.error('invalid homework or problem number')

    global VERBOSE, ALL, BUILD, COMPILER, GENERATE, TIMEOUT
    VERBOSE, ALL, BUILD, COMPILER, GENERATE, TIMEOUT = args.verbose, args.all, args.build, args.compiler, args.generate, args.timeout

    return args.hw, args.p

def read_list():
    with open(FILE_LIST) as file_list:
        lis = file_list.read()
        stus = re.findall(r'\d{8,10}', lis)
    return stus

def float_equal(my, your):
    return abs(my - your) * (10 ** 4) < max(abs(my), abs(your), 1)

def default_compare(my, your):
    if my == your:
        return True, 1
    else:
        return False, my, your

def match_level_compare(my, your):
    STRONG = 1
    NORMAL = 0.8
    WEAK = 0.6
    if my == your:
        return True, STRONG
    else:
        my_lines = [s.rstrip() for s in my.rstrip().split('\n')]
        your_lines = [s.rstrip() for s in your.rstrip().split('\n')]
        if my_lines == your_lines:
            return True, NORMAL, repr(my), repr(your)
        else:
            my_tokens = my.split()
            your_tokens = your.split()
            if my_tokens == your_tokens:
                return True, WEAK, repr(my), repr(your)
            else:
                return False, repr(my), repr(your)

def match_level_compare_p3(my, your):
    STRONG = 1
    NORMAL = 0.8
    WEAK = 0.6
    if my == your:
        return True, STRONG
    else:
        my_lines = [s.rstrip() for s in my.rstrip().split('\n')]
        your_lines = [s.rstrip() for s in your.rstrip().split('\n')]
        my_lines = [s for s in my_lines if s != '']
        your_lines = [s for s in your_lines if s != '']
        if my_lines == your_lines:
            return True, STRONG
        else:
            my_tokens = my.split()
            your_tokens = your.split()
            if my_tokens == your_tokens:
                return True, WEAK, repr(my), repr(your)
            else:
                return False, repr(my), repr(your)

def fetch_testcase(hw, p, num):
    ins = []
    outs = []
    for i in range(num):
        with open(FILE_IN_STYLE.format(hw, p, i)) as file_in, open(FILE_OUT_STYLE.format(hw, p, i)) as file_out:
            str_in = file_in.read()
            str_out = file_out.read()
            ins.append(str_in)
            outs.append(str_out)

    assert(len(ins) == num)
    assert(len(outs) == num)
    return ins, outs

def build(hw, p, src_file, exec_file, name = 'your program'):
    success = False
    try:
        print('Building {}...'.format(name))
        result = subprocess.run([COMPILER, src_file, '-o', exec_file] + COMPILER_OPTION)
        ret = result.returncode
    except:
        print('Failed to build {}: an error occurred.'.format(name))
    else:
        if ret != 0:
            print('Failed to build {}: exit code {}.'.format(name, ret))
        else:
            print('Successfully built {}.'.format(name))
            success = True

    print()
    return success

def generate(hw, p, num, exec_file):
    ins = []
    print('Generating output files...')
    if VERBOSE:
        print()

    for i in range(num):
        with open(FILE_IN_STYLE.format(hw, p, i)) as file_in, open(FILE_OUT_STYLE.format(hw, p, i), 'w') as file_out:
            str_in = file_in.read()
            try:
                result = subprocess.run(exec_file, input=str_in.encode(), stdout=subprocess.PIPE, timeout=TIMEOUT)
                str_out = result.stdout.decode()
            except subprocess.TimeoutExpired:
                if VERBOSE:
                    print('Test {} output not generated: time out.'.format(i))
            except:
                if VERBOSE:
                    print('Test {} output not generated: an error occurred.'.format(i))
            else:
                file_out.write(str_out)
                if VERBOSE:
                    print('Test {} output generated.'.format(i))

    if VERBOSE:
        print()
    print('All outputs generated.')
    print()

def grade(ins, outs, hw, p, num, exec_file, custom = 'default_compare', name = 'your program'):
    total_score = 0
    print('Grading {}...'.format(name))
    if VERBOSE:
        print()

    for i in range(num):
        try:
            your = subprocess.run(exec_file, input=ins[i].encode(), stdout=subprocess.PIPE, timeout=TIMEOUT)
            ret = your.returncode
        except subprocess.TimeoutExpired:
            if VERBOSE:
                print('Test {} failed: time out.'.format(i))
            continue
        except:
            if VERBOSE:
                print('Test {} failed: an error occurred.'.format(i))
            continue
        if ret != 0:
            if VERBOSE:
                print('Test {} failed: exit code {}.'.format(i, ret))
            continue

        my = outs[i]
        your = your.stdout.decode()
        my_repr, your_repr = repr(my), repr(your)
        compare = globals()[custom]
        result = compare(my, your)
        pass_score = 1
        if isinstance(result, tuple):
            if result[0]:
                assert(len(result) in (2,4))
                if len(result) == 2:
                    result, pass_score = result
                else:
                    result, pass_score, my_repr, your_repr = result
            else:
                result, my_repr, your_repr = result
        if result:
            total_score += pass_score

        if VERBOSE:
            if result:
                if pass_score >= 1:
                    print('Test {} passed.'.format(i))
                else:
                    print('Test {} partially passed. Score: {}'.format(i, pass_score))
                    print('  My output:   {}'.format(my_repr))
                    print('  Your output: {}'.format(your_repr))
            else:
                print('Test {} failed.'.format(i))
                print('  My output:   {}'.format(my_repr))
                print('  Your output: {}'.format(your_repr))

    if VERBOSE:
        print()
    print('Total score of {}: {:.1f} / {:.1f}'.format(name, total_score, num))
    print()

def main():
    hw, p = get_args()
    num, custom = HW_MAP[hw][p]
    stus = read_list() if ALL else ['your program']

    if GENERATE:
        if BUILD:
            src_file = REF_SRC_STYLE.format(hw, p)
            exec_file = REF_EXEC_STYLE.format(hw, p)
            build(hw, p, src_file, exec_file, name = 'reference program')
        generate(hw, p, num, exec_file)

    else:
        if ALL:
            src_file_base = ALL_STU_SRC_STYLE.format('{}', hw, p)
            exec_file_base = ALL_STU_EXEC_STYLE.format('{}', hw, p)
        else:
            src_file = STU_SRC_STYLE.format(hw, p)
            exec_file = STU_EXEC_STYLE.format(hw, p)

        for stu in stus:
            if ALL:
                src_file = src_file_base.format(stu)
                exec_file = exec_file_base.format(stu)
            if BUILD:
                success = build(hw, p, src_file, exec_file, name = stu)
                if not success:
                    continue
            ins, outs = fetch_testcase(hw, p, num)
            grade(ins, outs, hw, p, num, exec_file, custom = custom, name = stu)

if __name__ == '__main__':
    main()
