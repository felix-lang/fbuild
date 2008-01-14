import os
import types
import functools
import yaml

import fbuild
import fbuild.path
import fbuild.builders

# -----------------------------------------------------------------------------

class Builder(yaml.YAMLObject):
    def __init__(self, system):
        self.system = system

    def __setstate__(self, state):
        self.__init__(**state)

    def __getstate__(self):
        state = {'system': self.system}
        def f(cls):
            if cls == type:
                return

            try:
                state.update({k:getattr(self, k) for k in cls.yaml_state})
            except AttributeError:
                pass

            for c in cls.__bases__:
                f(c)
        f(self.__class__)

        return state

    def log(self, *args, **kwargs):
        return self.system.log(*args, **kwargs)

    def check(self, *args, **kwargs):
        return self.system.log.check(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self.system.execute(*args, **kwargs)

# -----------------------------------------------------------------------------

def test(msg, failed, color='green'):
    def decorator(func):
        @functools.wraps(func)
        def aux(system, *args, **kwds):
            system.log.check(0, msg)

            res =  func(system, *args, **kwds)
            if res:
                system.log(0, 'ok ' + str(res), color=color)
            else:
                system.log(0, failed, color='yellow')

            return res
        return aux
    return decorator


def find_program(system, *names):
    for name in names:
        system.log.check(0, 'checking for program ' + name)

        program = fbuild.path.find_in_paths(name)
        if program:
            system.log(0, 'ok %s' % program, color='green')
            return program
        else:
            system.log(0, 'not found', color='yellow')

    raise fbuild.ConfigFailed('failed to find any of ' + str(names))

# -----------------------------------------------------------------------------

class SimpleCommand(Builder):
    def __init__(self, system, exe,
            prefix='',
            suffix='',
            before_dst=None,
            color=None):
        super().__init__(system)

        self.exe = exe
        self.prefix = prefix
        self.suffix = suffix
        self.before_dst = before_dst
        self.color = color

    def __call__(self, dst, srcs,
            pre_flags=[],
            flags=[],
            post_flags=[],
            **kwargs):
        kwargs.setdefault('color', self.color)

        dst = fbuild.path.make_path(dst)

        dirname, basename = os.path.split(dst)
        dst = os.path.join(dirname, self.prefix + basename + self.suffix)

        cmd = self.exe[:]
        cmd.extend(pre_flags)

        if self.before_dst is not None:
            cmd.append(self.before_dst)

        cmd.append(dst)
        cmd.extend(fbuild.path.glob_paths(srcs))
        cmd.extend(flags)
        cmd.extend(post_flags)

        self.system.execute(cmd,
            (' '.join(self.exe), '%s -> %s' % (' '.join(srcs), dst)),
            **kwargs
        )

        return dst
