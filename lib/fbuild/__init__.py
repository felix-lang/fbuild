import os
import signal
import threading
import time

import fbuild.subprocess.killableprocess

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

class ExecutionTimedOut(ExecutionError):
    def __str__(self):
        if isinstance(self.cmd, str):
            cmd = self.cmd
        else:
            cmd = ' '.join(self.cmd)

        return 'Timed out running %r exited with %d' % (cmd, self.returncode)

# ------------------------------------------------------------------------------

import fbuild.console
logger = fbuild.console.Log()

# ------------------------------------------------------------------------------

def execute(cmd,
        msg1=None,
        msg2=None,
        color=None,
        quieter=0,
        stdout_quieter=None,
        stderr_quieter=None,
        input=None,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=None,
        **kwargs):
    """Execute the command and return the output."""

    if isinstance(cmd, str):
        cmd_string = cmd
    else:
        cmd_string = ' '.join(cmd)

    if stdout_quieter is None:
        stdout_quieter = quieter

    if stderr_quieter is None:
        stderr_quieter = quieter

    logger.write('%-10s: starting %r\n' %
        (threading.current_thread().name, cmd_string),
        verbose=4,
        buffer=False)

    if msg1:
        if msg2:
            logger.check(' * ' + str(msg1), str(msg2),
                color=color,
                verbose=stdout_quieter)
        else:
            logger.check(' * ' + str(msg1),
                color=color,
                verbose=stdout_quieter)

    # Define a function that gets called if execution times out. We will
    # raise an exception if the timeout occurs.
    if timeout:
        timed_out = False
        def timeout_function(p):
            nonlocal timed_out
            timed_out = True
            p.kill(group=True)

    starttime = time.time()
    try:
        p = fbuild.subprocess.killableprocess.Popen(cmd,
            stdin=subprocess.PIPE if input else stdin,
            stdout=stdout,
            stderr=stderr,
            **kwargs)

        try:
            if timeout:
                timer = threading.Timer(timeout, timeout_function, (p,))
                timer.start()

            stdout, stderr = p.communicate(input)
            returncode = p.wait()
        except KeyboardInterrupt:
            # Make sure if we get a keyboard interrupt to kill the process.
            p.kill(group=True)
            raise
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
            logger.log(stdout.rstrip().decode(), verbose=stdout_quieter)
        except UnicodeDecodeError:
            logger.log(repr(stdout.rstrip()), verbose=stdout_quieter)
    if stderr:
        try:
            logger.log(stderr.rstrip().decode(), verbose=stderr_quieter)
        except UnicodeDecodeError:
            logger.log(repr(stderr.rstrip()), verbose=stderr_quieter)

    logger.log(
        ' - exit %d, %.2f sec' % (returncode, endtime - starttime),
        verbose=2)

    if timeout and timed_out:
        raise ExecutionTimedOut(cmd, stdout, stderr, returncode)
    elif returncode:
        raise ExecutionError(cmd, stdout, stderr, returncode)

    return stdout, stderr
