# -----------------------------------------------------------------------------

class ExecutionError(Exception):
    def __init__(self, cmd, stdout, stderr, returncode):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __str__(self):
        if isinstance(cmd, types.StringTypes):
            cmd = self.cmd
        else:
            cmd = ' '.join(self.cmd)

        return 'Error running %r exited with %d' % (cmd, self.returncode)

class ConfigFailed(Exception):
    pass

# -----------------------------------------------------------------------------

def _import_string(s):
    if isinstance(s, basestring):
        return getattr(__import__(s), s.rsplit('.')[-1])
    return s

builder_cache = {}

def configure(config_builder, phase):
    config_builder = _import_string(config_builder)

    key = config_builder.__module__ + '.' + config_builder.__name__
    builder = builder_cache.setdefault(key, {}).get(phase)

    if builder is None:
        builder = config_builder(phase)
        builder_cache[config_builder][phase] = builder

    return builder

def make_phase(name, packages, config=None):
    packages = [_import_string(p) for p in packages]

    if config is not None:
        config = _import_string(config)
