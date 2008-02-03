import time
import subprocess
import functools
import yaml

from . import console
from . import scheduler
from . import ExecutionError, ConfigFailed
from .path import import_function

# -----------------------------------------------------------------------------

class ConfigGroup(yaml.YAMLObject):
    yaml_tag = '!ConfigGroup'

    def __init__(self, system, config={}):
        self.system = system
        for k, v in config.items():
            setattr(self, k, v)

    def __getstate__(self):
        return {k:v for k,v in self.__dict__.items() if k != 'system'}

    def configure(self, *args, **kwargs):
        return self.system._configure(self, *args, **kwargs)

    def config_group(self, *args, **kwargs):
        return self.system._config_group(self, *args, **kwargs)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__dict__)

    def __bool__(self):
        return 1 < len(self.__dict__)

    def log(self, *args, **kwargs):
        return self.system.log(*args, **kwargs)

    def check(self, *args, **kwargs):
        return self.system.check(*args, **kwargs)

    def run_tests(self, tests):
        for test in tests:
            test = import_function(test)
            test(self)

    def run_optional_tests(self, tests):
        for test in tests:
            test = import_function(test)
            try:
                test(self)
            except ConfigFailed:
                pass

# -----------------------------------------------------------------------------

class System(yaml.YAMLObject):
    yaml_tag = '!System'

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
            self.config = ConfigGroup(self)
            self.config_dirty = True

        self.configfile = configfile
        self.threadcount = threadcount
        self.verbose = verbose
        self.logger = console.Log(self, logfile)
        self.nocolor = nocolor
        self.show_threads = show_threads

        self.scheduler = scheduler.Scheduler(threadcount)

    def check(self, *args, **kwargs):
        return self.logger.check(*args, **kwargs)

    def log(self, *args, **kwargs):
        return self.logger.log(*args, **kwargs)

    def load_yaml_config(self, file):
        def system(loader, node):
            self.config = ConfigGroup(self, loader.construct_mapping(node))
            return self

        def config_group(loader, node):
            return ConfigGroup(self, loader.construct_mapping(node))

        yaml_loader = yaml.Loader(file)
        yaml_loader.add_constructor('!System', system)
        yaml_loader.add_constructor('!ConfigGroup', config_group)
        yaml_loader.get_single_data()
        self.config_dirty = False

    def __getstate__(self):
        return self.config.__getstate__()

    # -------------------------------------------------------------------------

    def configure(self, *args, **kwargs):
        return self._configure(self.config, *args, **kwargs)

    def config_group(self, *args, **kwargs):
        return self._config_group(self.config, *args, **kwargs)

    # -------------------------------------------------------------------------

    def _configure(self, conf, name, function, *args, **kwargs):
        *names, name = name.split('.')
        for n in names:
            try:
                conf = getattr(conf, n)
            except AttributeError:
                setattr(conf, n, ConfigGroup(self))
                conf = getattr(conf, n)

        try:
            return getattr(conf, name)
        except AttributeError:
            self.config_dirty = True
            setattr(conf, name, import_function(function)(*args, **kwargs))
            return getattr(conf, name)

        return result

    def _config_group(self, conf, name):
        for n in name.split('.'):
            c = conf
            try:
                conf = getattr(conf, n)
            except AttributeError:
                setattr(conf, n, ConfigGroup(self))
                conf = getattr(conf, n)

        return conf

    # -------------------------------------------------------------------------

    def join(self):
        self.scheduler.join()

    def future(self, f, *args, **kwargs):
        @functools.wraps(f)
        def wrapper():
            self.logger.push_thread()
            try:
                return f(*args, **kwargs)
            finally:
                self.logger.pop_thread()

        return self.scheduler.future(wrapper)

    # -------------------------------------------------------------------------

    def execute(self, cmd,
            msg1=None,
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
            self.logger.write('starting %r\n' % cmd_string,
                verbose=4,
                buffer=False,
            )
        else:
            self.logger.write('%-10s: starting %r\n' %
                (threading.currentThread().getName(), cmd_string),
                verbose=4,
                buffer=False,
            )

        starttime = time.time()
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, **kwargs)
        stdout, stderr = p.communicate()
        returncode = p.wait()
        endtime = time.time()

        if msg1:
            if msg2:
                self.check(' * ' + str(msg1), str(msg2),
                    color=color,
                    verbose=quieter)
            else:
                self.check(' * ' + str(msg1), color=color, verbose=quieter)

        if returncode:
            self.log(' + ' + cmd_string, verbose=quieter)
        else:
            self.log(' + ' + cmd_string, verbose=1)

        if stdout: self.log(stdout.rstrip().decode('utf-8'), verbose=quieter)
        if stderr: self.log(stderr.rstrip().decode('utf-8'), verbose=quieter)

        self.log(' - exit %d, %.2f sec' % (returncode, endtime - starttime),
            verbose=2,
        )

        if returncode:
            raise ExecutionError(cmd, stdout, stderr, returncode)

        return stdout, stderr

    # -------------------------------------------------------------------------

    def configure_package(self, package, *args, **kwargs):
        try:
            package.configure(self, *args, **kwargs)
        except ConfigFailed as e:
            self.log(e, color='red')
            raise e from e

        if self.config_dirty:
            self.log('saving config')
            with open(self.configfile, 'w') as f:
                yaml.dump(self, f)

            self.log('-' * 79, color='blue')

    def run_package(self, package, *args, **kwargs):
        try:
            if not self.config:
                self.configure_package(package, *args, **kwargs)

            package.build(self, *args, **kwargs)
        finally:
            self.join()
