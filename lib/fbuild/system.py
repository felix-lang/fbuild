import os
import functools
import threading
import yaml

from fbuild import ExecutionError, ConfigFailed
from fbuild.scheduler import Scheduler
from fbuild.path import import_function

# -----------------------------------------------------------------------------

class System:
    def __init__(self, configfile, *,
            threadcount=0,
            force_configuration=False):
        self.configfile = configfile

        if force_configuration or not os.path.exists(configfile):
            self.config = {}
            self.config_dirty = True
        else:
            with open(configfile) as f:
                self.config = yaml.load(f)

        self.threadcount = threadcount
        self.scheduler = Scheduler(threadcount)

    # -------------------------------------------------------------------------

    def join(self):
        self.scheduler.join()

    def future(self, f, *args, **kwargs):
        from fbuild import logger

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger.push_thread()
            try:
                return f(*args, **kwargs)
            finally:
                logger.pop_thread()

        return self.scheduler.future(wrapper, *args, **kwargs)

    # -------------------------------------------------------------------------

    def configure_package(self, package, *args, **kwargs):
        from fbuild import logger

        try:
            package.configure(self.config, *args, **kwargs)
        except ConfigFailed as e:
            logger.log(e, color='red')
            raise e from e

        if self.config_dirty:
            logger.log('saving config')
            with open(self.configfile, 'w') as f:
                yaml.dump(self.config, f)

            logger.log('-' * 79, color='blue')

    def run_package(self, package, *args, **kwargs):
        try:
            if not self.config:
                self.configure_package(package, *args, **kwargs)

            package.build(self.config, *args, **kwargs)
        finally:
            self.join()

def make_system(*args, **kwargs):
    global system
    system = System(*args, **kwargs)
