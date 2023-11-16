# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Utility functions.
"""

import os
import re
import ctypes
import operator
import socket
import tempfile

import jinja2

from typing import Any, Iterator, Tuple, List
from functools import reduce, partial


class ColorText(object):
    """
    Terminal text color.
    """

    COLORS = {
        'red': '31m',
        'green': '32m',
        'yellow': '33m'
    }

    @staticmethod
    def wrap(s, color):
        """
        Color the str `s`.
        """
        code = ColorText.COLORS.get(color, None)
        if not code:
            raise ValueError('Not supported color: %s' % color)
        return '\033[%s%s\033[39m' % (code, s)


def xprint(*values, **kwargs) -> None:
    """
    Print function for xbot.

    :param values: values to print.
    :param color: color of values.
    :param do_exit: exit after print.
    :param exit_code: exit code, default -1.
    """
    color = kwargs.pop('color', None)
    do_exit = kwargs.pop('do_exit', False)
    exit_code = kwargs.pop('exit_code', -1)
    if color:
        values = [ColorText.wrap(v, color) for v in values]
    print(*values, **kwargs)
    if do_exit:
        exit(exit_code)


printerr = partial(xprint, 'error:', color='red', do_exit=True)


def render_write(template: str, outfile: str, **kwargs) -> None:
    """
    Render the `template` and write to `outfile`.
    
    :param template: html template.
    :param outfile: output file.
    """
    rendered_content = ''
    with open(template) as fp:
        tpl = jinja2.Template(fp.read())
        rendered_content = tpl.render(**kwargs)
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    with open(outfile, 'w') as fp:
        fp.write(rendered_content)


def stop_thread(thread, exc=SystemExit) -> None:
    """
    Stop thread by raising an exception.
    
    :param thread: Thread instance.
    :param exc: Exception to raise.
    :raises SystemError: If stop thread failed.
    """
    r = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), ctypes.py_object(exc))
    if r == 0:
        raise ValueError("Invalid thread id '%s'" % thread.ident)
    if r != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), None)
        raise SystemError("Stop thread '%s' failed" % thread.name)


def parse_deepkey(deepkey: str, sep: str = '.') -> list:
    """
    Parse deepkey to list.

    >>> parse_deepkey('a.b1')
    ['a', 'b1']
    >>> parse_deepkey('a.b2[0]')
    ['a', 'b2', 0]
    >>> parse_deepkey('a.b2[0].c2')
    ['a', 'b2', 0, 'c2']

    :param deepkey: deepkey string.
    :param sep: separator.
    :return: list of keys.
    """
    keys = []
    for k in re.split(r'%s|\[' % re.escape(sep), deepkey):
        if k.endswith(']') and k[:-1].isdigit():
            keys.append(int(k[:-1]))
        else:
            keys.append(k)
    return keys


def deepget(obj, deepkey: str, sep: str = '.') -> Any:
    """
    Deep get value from object.

    >>> d = {
    ...     'a': {
    ...         'b1': 'c',
    ...         'b2': [1, 2, 3]
    ...      }
    ... }
    >>> deepget(d, 'a.b1')
    'c'
    >>> deepget(d, 'a.b2[0]')
    1

    :param obj: object.
    :param deepkey: deepkey string.
    :param sep: separator for deepkey.
    :return: value.
    """
    keys = parse_deepkey(deepkey, sep)
    return reduce(operator.getitem, keys, obj)


def deepset(obj: Any, deepkey: str, value: Any, sep: str = '.') -> None:
    """
    Deep set value to object.
    Create path if not exists(except for path with index, e.g. a.b[0])

    >>> d = {
    ...     'a': {
    ...         'b1': 'c',
    ...         'b2': [1, 2, 3]
    ...      }
    ... }
    >>> deepset(d, 'a.b1', 'd')
    >>> d
    {'a': {'b1': 'd', 'b2': [1, 2, 3]}}
    >>> deepset(d, 'a.b2[0]', '-1')
    >>> d
    {'a': {'b1': 'd', 'b2': ['-1', 2, 3]}}
    >>> deepset(d, 'i.j', 'x')
    >>> d
    {'a': {'b1': 'd', 'b2': ['-1', 2, 3]}, 'i': {'j': 'x'}}

    :param obj: Object.
    :param deepkey: deepkey string.
    :param value: value to set.
    :param sep: separator for deepkey.
    """
    keys = parse_deepkey(deepkey, sep)
    for k in keys[:-1]:
        try:
            obj = operator.getitem(obj, k)
        except KeyError:
            obj[k] = {}
            obj = obj[k]
    operator.setitem(obj, keys[-1], value)


def ip_reachable(ip: str) -> bool:
    """
    Check if IP address is reachable.

    :param ip: IP address.
    :return: True if reachable, else False.
    """
    try:
        conn = socket.create_connection((ip, 22), 0.1)
        conn.close()
        return True
    except ConnectionRefusedError:
        return True
    except:
        return False


def port_opened(ip: str, port: int) -> bool:
    """
    Check if port is opened.

    :param ip: IP address.
    :param port: Port number.
    :return: True if opened, else False.
    """
    try:
        conn = socket.create_connection((ip, port), 0.1)
        conn.close()
        return True
    except:
        return False
    

def wrapstr(s: str, title: str = '') -> str:
    """
    Wrap str with character borders.

    >>> print(wrapstr('hello world'))
    +-------------+
    | hello world |
    +-------------+
    >>> print(wrapstr('hello world\\nhello world2'))
    +--------------+
    | hello world  |
    | hello world2 |
    +--------------+
    >>> print(wrapstr('hello world', title='test'))
    +-----test----+
    | hello world |
    +-------------+

    :param s: 字符串。
    :param title: 标题。
    """
    lines = s.splitlines()
    width = max(len(line) for line in lines + [title])
    return '\n'.join([
        '+' + title.center(width + 2, '-') + '+',
        *('| %s |' % line.ljust(width) for line in lines),
        '+' + '-' * (width + 2) + '+'
    ])


def ordered_walk(path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
    """
    Similar to os.walk, but accessed in name order.

    >>> tmpdir = tempfile.mkdtemp()
    >>> dir1 = os.path.join(tmpdir, 'dir1')
    >>> dir2 = os.path.join(tmpdir, 'dir2')
    >>> file1 = os.path.join(tmpdir, 'file1')
    >>> file2 = os.path.join(tmpdir, 'file2')
    >>> file1_1 = os.path.join(dir1, 'file1_1')
    >>> file1_2 = os.path.join(dir1, 'file1_2')
    >>> file2_1 = os.path.join(dir2, 'file2_1')
    >>> file2_2 = os.path.join(dir2, 'file2_2')
    >>> os.makedirs(os.path.join(tmpdir, 'dir1'))
    >>> os.makedirs(os.path.join(tmpdir, 'dir2'))
    >>> for file in [file1, file2, file1_1, file1_2, file2_1, file2_2]:
    ...     with open(file, 'w') as fp:
    ...         _ = fp.write('hello world')
    >>> for top, dirs, files in ordered_walk(tmpdir):
    ...     print(f'dirs: {dirs}, files: {files}')
    dirs: ['dir1', 'dir2'], files: ['file1', 'file2']
    dirs: [], files: ['file1_1', 'file1_2']
    dirs: [], files: ['file2_1', 'file2_2']

    :param path: path to walk.
    :yield: (top, dirs, files)
    """
    top, dirs, files = path, [], []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_dir():
                dirs.append(entry.name)
            elif entry.is_file():
                files.append(entry.name)
    dirs.sort()
    files.sort()
    yield top, dirs, files
    for d in dirs:
        for t in ordered_walk(os.path.join(path, d)):
            yield t
