import time
import subprocess
import threading

# -----------------------------------------------------------------------------

class ConfigFailed(Exception):
    pass

class ExecutionError(Exception):
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

        lines = ['Error running %r exited with %d' % (cmd, self.returncode)]
        if self.stdout: lines.append(self.stdout.decode('utf-8'))
        if self.stderr: lines.append(self.stderr.decode('utf-8'))
        return '\n'.join(lines)

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
        stderr=subprocess.STDOUT,
        **kwargs):
    from fbuild.system import system

    if isinstance(cmd, str):
        cmd_string = cmd
    else:
        cmd_string = ' '.join(cmd)

    if system.threadcount <= 1:
        logger.write('starting %r\n' % cmd_string,
            verbose=4,
            buffer=False)
    else:
        logger.write('%-10s: starting %r\n' %
            (threading.currentThread().getName(), cmd_string),
            verbose=4,
            buffer=False)

    starttime = time.time()
    p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, **kwargs)
    stdout, stderr = p.communicate()
    returncode = p.wait()
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
