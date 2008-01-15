import time
import subprocess
import functools
import yaml

from . import console
from . import scheduler
from . import ExecutionError, ConfigFailed

# -----------------------------------------------------------------------------

class ConfigGroup(yaml.YAMLObject):
    yaml_tag = '!ConfigGroup'

    def __init__(self, system, config=None):
        self.system = system
        self.config = config or {}

    def __getstate__(self):
        return self.config

    def configure(self, *args, **kwargs):
        return self.system._configure(self, *args, **kwargs)

    def subconfigure(self, *args, **kwargs):
        return self.system._subconfigure(self, *args, **kwargs)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __getattr__(self, *args, **kwargs):
        return getattr(self.system, *args, **kwargs)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.config)

    def __bool__(self):
        return bool(self.config)

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
        self.log = console.Log(self, logfile)
        self.nocolor = nocolor
        self.show_threads = show_threads

        self.scheduler = scheduler.Scheduler(threadcount)


    def load_yaml_config(self, file):
        def system(loader, node):
            self.config = loader.construct_mapping(node)
            return self

        def config_group(loader, node):
            return ConfigGroup(self, loader.construct_mapping(node))

        yaml_loader = yaml.Loader(file)
        yaml_loader.add_constructor('!System', system)
        yaml_loader.add_constructor('!ConfigGroup', config_group)
        yaml_loader.get_single_data()
        self.config_dirty = False


    def __getstate__(self):
        return self.config.config

    # -------------------------------------------------------------------------

    def configure(self, *args, **kwargs):
        return self._configure(self.config, *args, **kwargs)


    def subconfigure(self, *args, **kwargs):
        return self._subconfigure(self.config, *args, **kwargs)

    # -------------------------------------------------------------------------

    def _import(self, function):
        if isinstance(function, str):
            m, f = function.rsplit('.', 1)
            try:
                return getattr(__import__(m, {}, {}, ['']), f)
            except SyntaxError as e:
                e.msg = '%s: %s' % (function, e.msg)
                raise e

        return function


    def _configure(self, conf, name, function, *args, **kwargs):
        *names, name = name.split('.')
        for n in names:
            try:
                conf = conf[n]
            except KeyError:
                conf[n] = ConfigGroup(self)
                conf = conf[n]

        try:
            result = conf[name]
        except KeyError:
            self.config_dirty = True
            result = conf[name] = self._import(function)(*args, **kwargs)

        return result


    def _subconfigure(self, conf, name, function, *args, **kwargs):
        if name:
            for n in name.split('.'):
                c = conf
                try:
                    conf = conf[n]
                except KeyError:
                    conf[n] = ConfigGroup(self)
                    conf = conf[n]

        self.config_dirty = True
        self._import(function)(conf, *args, **kwargs)

        return conf

    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------

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
                self.log.check(' * ' + msg, color=color, verbose=quieter)
            else:
                self.log.check(' * ' + msg1, msg2, color=color, verbose=quieter)

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
