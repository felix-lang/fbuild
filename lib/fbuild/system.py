import time
import optparse
import subprocess
import functools
import yaml

from . import console
from . import scheduler
from . import ExecutionError, ConfigFailed

# -----------------------------------------------------------------------------

class ConfigGroup:
    def __init__(self, system, group):
        self.system = system
        self.group = group

    def make_config_subgroup(self, name):
        return self.system._make_config_subgroup(self.group, name)

    def configure(self, *args, **kwargs):
        return self.system._configure(self.group, *args, **kwargs)

    def subconfigure(self, *args, **kwargs):
        return self.system._subconfigure(self, *args, **kwargs)

    def __getattr__(self, *args, **kwargs):
        return getattr(self.system, *args, **kwargs)

# -----------------------------------------------------------------------------

class System(yaml.YAMLObject):
    cmdline_options = [
        optparse.make_option('-v', '--verbose',
            action='count',
            default=0,
            help='print out extra debugging info'),
        optparse.make_option('--show',
            action='count',
            default=1,
            help='print out extra debugging info'),
        optparse.make_option('-j', '--jobs',
            dest='threadcount',
            metavar='N',
            type='int',
            default=1,
            help='Allow N jobs at once'),
        optparse.make_option('--nocolor',
            action='store_true',
            default=False,
            help='Do not use colors'),
    ]

    yaml_tag = '!fbuild.system.System'

    def __init__(self, configfile,
            threadcount=0,
            verbose=0,
            logfile='fbuild.log',
            nocolor=False,
            show_threads=False):
        try:
            with open(configfile) as f:
                self.load_yaml_config(f)
        except IOError:
            self.config = {}
            self.config_dirty = True

        self.configfile = configfile
        self.threadcount = threadcount
        self.verbose = verbose
        self.log = console.Log(self, logfile)
        self.nocolor = nocolor
        self.show_threads = show_threads

        self.scheduler = scheduler.Scheduler(threadcount)

    def load_yaml_config(self, file):
        def constructor(loader, node):
            self.config = loader.construct_mapping(node)
            return self

        yaml_loader = yaml.Loader(file)
        yaml_loader.add_constructor('!fbuild.system.System', constructor)
        yaml_loader.get_single_data()
        self.config_dirty = False


    def __getstate__(self):
        return self.config


    def make_config_subgroup(self, name):
        return self._make_config_subgroup(self.config, name)


    def _make_config_subgroup(self, group, name):
        group.setdefault(name, {})
        return ConfigGroup(self, group[name])


    def configure(self, *args, **kwargs):
        return self._configure(self.config, *args, **kwargs)


    def _configure(self, group, name, function, *args, **kwargs):
        try:
            return group[name]
        except KeyError:
            pass

        self.config_dirty = True
        if isinstance(function, str):
            m, f = function.rsplit('.', 1)
            function = getattr(__import__(m, {}, {}, ['']), f)
        result = function(*args, **kwargs)

        group[name] = result

        return result


    def subconfigure(self, function, *args, **kwargs):
        return self._subconfigure(self, function, *args, **kwargs)


    def _subconfigure(self, group, function, *args, **kwargs):
        if isinstance(function, str):
            m, f = function.rsplit('.', 1)
            function = getattr(__import__(m, {}, {}, ['']), f)
        return function(group, *args, **kwargs)


    def join(self):
        self.scheduler.join()


    def future(self, f, *args, **kwargs):
        @functools.wraps(f)
        def wrapper():
            self.log.push_thread()
            try:
                return f(*args, **kwargs)
            finally:
                self.log.pop_thread()

        return self.scheduler.future(wrapper)


    def execute(self, cmd,
            msg=None,
            msg2=None,
            color=None,
            quieter=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs):
        if isinstance(cmd, str):
            cmd_string = cmd
        else:
            cmd_string = ' '.join(cmd)

        if self.threadcount <= 1:
            self.log.write('starting %r\n' % cmd_string,
                verbose=4,
                buffer=False,
            )
        else:
            self.log.write('%-10s: starting %r\n' %
                (threading.currentThread().getName(), cmd_string),
                verbose=4,
                buffer=False,
            )

        starttime = time.time()
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, **kwargs)
        stdout, stderr = p.communicate()
        returncode = p.wait()
        endtime = time.time()

        if msg:
            try:
                msg1, msg2 = msg
            except TypeError:
                self.log.check(quieter, ' * ' + msg, color=color)
            else:
                self.log.check(quieter, ' * ' + msg1, msg2, color=color)

        self.log(1, ' + ' + cmd_string)

        if stdout: self.log(0 + quieter, stdout.rstrip().decode('utf-8'))
        if stderr: self.log(0 + quieter, stderr.rstrip().decode('utf-8'))

        self.log(2, ' - exit %d, %.2f sec' % (
            returncode,
            endtime - starttime,
        ))

        if returncode:
            raise ExecutionError(cmd, stdout, stderr, returncode)

        return stdout, stderr

    def run(self, package, *args, **kwargs):
        try:
            try:
                package.configure(self, *args, **kwargs)
                package.build(self, *args, **kwargs)
            finally:
                self.join()
        except ConfigFailed as e:
            self.log(0, e, color='red')
            raise e from e
        else:
            if self.config_dirty:
                self.log(0, 'saving config')
                with open(self.configfile, 'w') as f:
                    yaml.dump(self, f)
