import time
import subprocess
import threading

# -----------------------------------------------------------------------------

# just share Path with everything that uses fbuild
from fbuild.path import Path

# -----------------------------------------------------------------------------

class Error(Exception):
    pass

class ConfigFailed(Error):
    pass

class ExecutionError(Error):
    def __init__(self, cmd, stdout, stderr, returncode):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __str__(self):
        if isinstance(self.cmd, str):
            cmd = self.cmd
        else:
            cmd = ' '.join(self.cmd)

        return 'Error running %r exited with %d' % (cmd, self.returncode)

# -----------------------------------------------------------------------------

import fbuild.console
logger = fbuild.console.Log()

# -----------------------------------------------------------------------------

def execute(cmd,
        msg1=None,
        msg2=None,
        color=None,
        quieter=0,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs):
    if isinstance(cmd, str):
        cmd_string = cmd
    else:
        cmd_string = ' '.join(cmd)

    logger.write('%-10s: starting %r\n' %
        (threading.current_thread().get_name(), cmd_string),
        verbose=4,
        buffer=False)

    starttime = time.time()
    try:
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, **kwargs)
        stdout, stderr = p.communicate()
        returncode = p.wait()
    except OSError as e:
        # flush the logger
        logger.log('command failed: ' + cmd_string, color='red')
        raise e from e
    endtime = time.time()

    if msg1:
        if msg2:
            logger.check(' * ' + str(msg1), str(msg2),
                color=color,
                verbose=quieter)
        else:
            logger.check(' * ' + str(msg1),
                color=color,
                verbose=quieter)

    if returncode:
        logger.log(' + ' + cmd_string, verbose=quieter)
    else:
        logger.log(' + ' + cmd_string, verbose=1)

    if stdout: logger.log(stdout.rstrip().decode('utf-8'), verbose=quieter)
    if stderr: logger.log(stderr.rstrip().decode('utf-8'), verbose=quieter)

    logger.log(
        ' - exit %d, %.2f sec' % (returncode, endtime - starttime),
        verbose=2)

    if returncode:
        raise ExecutionError(cmd, stdout, stderr, returncode)

    return stdout, stderr

# -----------------------------------------------------------------------------

class Record(dict):
    def __setattr__(self, key, value):
        'Allow setting items as if they were attributes.'

        self[key] = value

    def __getattr__(self, key):
        'Allow items to be exposed as attributes.'

        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e) from e
