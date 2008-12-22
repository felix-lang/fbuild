import time
import subprocess
import threading

# ------------------------------------------------------------------------------

class Error(Exception):
    pass

class ConfigFailed(Error):
    pass

class ExecutionError(Error):
    def __init__(self, cmd='', stdout='', stderr='', returncode=-1):
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

# ------------------------------------------------------------------------------

import fbuild.console
logger = fbuild.console.Log()

# ------------------------------------------------------------------------------

def execute(cmd,
        msg1=None,
        msg2=None,
        color=None,
        quieter=0,
        input=None,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=None,
        **kwargs):
    if isinstance(cmd, str):
        cmd_string = cmd
    else:
        cmd_string = ' '.join(cmd)

    logger.write('%-10s: starting %r\n' %
        (threading.current_thread().name, cmd_string),
        verbose=4,
        buffer=False)

    if msg1:
        if msg2:
            logger.check(' * ' + str(msg1), str(msg2),
                color=color,
                verbose=quieter)
        else:
            logger.check(' * ' + str(msg1),
                color=color,
                verbose=quieter)

    starttime = time.time()
    try:
        p = subprocess.Popen(cmd,
            stdin=subprocess.PIPE if input else stdin,
            stdout=stdout,
            stderr=stderr,
            **kwargs)

        if timeout:
            timer = threading.Timer(timeout, p.kill)
            timer.start()

        stdout, stderr = p.communicate(input)
        returncode = p.wait()
    except OSError as e:
        # flush the logger
        logger.log('command failed: ' + cmd_string, color='red')
        raise e from e
    finally:
        if timeout:
            timer.cancel()
    endtime = time.time()

    if returncode:
        logger.log(' + ' + cmd_string, verbose=quieter)
    else:
        logger.log(' + ' + cmd_string, verbose=1)

    if stdout:
        try:
            logger.log(stdout.rstrip().decode('utf-8'), verbose=quieter)
        except UnicodeDecodeError:
            logger.log(repr(stdout.rstrip()), verbose=quieter)
    if stderr:
        try:
            logger.log(stderr.rstrip().decode('utf-8'), verbose=quieter)
        except UnicodeDecodeError:
            logger.log(repr(stderr.rstrip()), verbose=quieter)

    logger.log(
        ' - exit %d, %.2f sec' % (returncode, endtime - starttime),
        verbose=2)

    if returncode:
        raise ExecutionError(cmd, stdout, stderr, returncode)

    return stdout, stderr

# ------------------------------------------------------------------------------

import fbuild.environment
env = fbuild.environment.Environment()
