# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
命令行接口。
"""

import os
import sys
import shutil
import argparse

from importlib import import_module

from xbot.version import __version__
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.runner import Runner
from xbot.report import gen_report
from xbot.utils import printerr, xprint
from xbot.common import INIT_DIR


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。
    """
    parser = argparse.ArgumentParser(prog='xbot')
    parser.add_argument('command', choices=['init', 'run'])
    parser.add_argument('-d', '--directory', required=('init' in sys.argv), 
                        help='directory to init (required by `init` command)')
    parser.add_argument('-b', '--testbed', required=('run' in sys.argv), 
                        help='testbed filepath (required by `run` command)')
    parser.add_argument('-s', '--testset', required=('run' in sys.argv), 
                        help='testset filepath (required by `run` command)')
    parser.add_argument('-v', '--version', action='version', version=f'xbot {__version__}')
    return parser


def init(directory: str) -> None:
    """
    初始化测试项目目录。

    :param directory: 待初始化的目录。
    """
    if os.path.exists(directory):
        printerr('%s already exists' % directory)
    shutil.copytree(INIT_DIR, directory)
    xprint('Initialized %s' % directory)


def is_projdir(directory: str) -> bool:
    """
    检测当前目录是否为测试项目目录。

    :param directory: 待检测的目录。
    """
    return os.path.exists(os.path.join(directory, 'testcases'))
    

def run(testbed: str, testset: str) -> None:
    """
    执行测试。

    :param testbed: 测试床文件。
    :param testset: 测试床文件。
    """
    if not is_projdir(os.getcwd()):
        printerr("No `testcases` directory in current directory, "
                 "maybe current is not a project directory.")
    sys.path.insert(0, os.getcwd())
    tb = import_module('lib.testbed').TestBed(testbed)
    ts = TestSet(testset)
    runner = Runner(tb, ts)
    logdir = runner.run()
    xprint('Generating report...  ', end='')
    report_filepath, is_allpassed = gen_report(logdir)
    xprint(report_filepath, '\n', color='green', 
           do_exit=True, exit_code=(not is_allpassed))


def main() -> None:
    """
    入口函数。
    """
    parser = create_parser()
    args = parser.parse_args()
    if args.command == 'init':
        init(args.directory)
    elif args.command == 'run':
        run(args.testbed, args.testset)



if __name__ == '__main__':
    main()
