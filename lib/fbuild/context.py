import os
import signal
import threading
import time

import fbuild
import fbuild.console
import fbuild.db
import fbuild.path
import fbuild.sched
import fbuild.subprocess.killableprocess

# ------------------------------------------------------------------------------

class Context:
    def __init__(self, options, args):
        # Convert the paths to Path objects.
        options.buildroot = fbuild.path.Path(options.buildroot)
        options.state_file = options.buildroot / options.state_file

        self.logger = fbuild.console.Log(
            verbose=options.verbose,
            nocolor=options.nocolor,
            threadcount=options.threadcount,
            show_threads=options.show_threads)

        self.db = fbuild.db.Database(self)
        self.scheduler = fbuild.sched.Scheduler(self.logger, options.threadcount)

        self.options = options
        self.args = args

    @property
    def buildroot(self):
        return self.options.buildroot

    def create_buildroot(self):
        # Make sure the buildroot exists before running.
        self.buildroot.makedirs()

        # Load the logger options into the logger.
        self.logger.file = open(
            self.options.buildroot / self.options.log_file, 'w')

        # Make sure the state file directory exists.
        self.options.state_file.parent.makedirs()

    def load_configuration(self):
        # Optionally do `not` load the old database.
        if not self.options.force_configuration and \
                self.options.state_file.exists():
            # We aren't reconfiguring, so load the old database.
            self.db.load(self.options.state_file)

    def shutdown(self):
        self.scheduler.shutdown()

    def save_configuration(self):
        # Optionally do `not` save the database.
        if not self.options.do_not_save_database:
            # Remove the signal handler so that we can't interrupt saving the
            # db.
            prev_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                self.db.save(self.options.state_file)
            finally:
                signal.signal(signal.SIGINT, prev_handler)

    # --------------------------------------------------------------------------
    # Logging wrapper functions

#    def log(self, *args, **kwargs):
#        return self.logger.log(*args, **kwargs)
#
#    def check(self, *args, **kwargs):
#        return self.logger.check(*args, **kwargs)
#
#    def passed(self, *args, **kwargs):
#        return self.logger.passed(*args, **kwargs)
#
#    def failed(self, *args, **kwargs):
#        return self.logger.failed(*args, **kwargs)

    # --------------------------------------------------------------------------

    def execute(self, cmd,
            msg1=None,
            msg2=None,
            color=None,
            quieter=0,
            stdout_quieter=None,
            stderr_quieter=None,
            input=None,
            stdin=None,
            stdout=fbuild.subprocess.PIPE,
            stderr=fbuild.subprocess.PIPE,
            timeout=None,
            env=None,
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

        # Windows needs something in the environment, so for the moment we'll
        # just make sure everything is passed on to the executable.
        if env is None:
            env = os.environ
        else:
            env = dict(os.environ, **env)

        self.logger.write('%-10s: starting %r\n' %
            (threading.current_thread().name, cmd_string),
            verbose=4,
            buffer=False)

        if msg1:
            if msg2:
                self.logger.check(' * ' + str(msg1), str(msg2),
                    color=color,
                    verbose=quieter)
            else:
                self.logger.check(' * ' + str(msg1),
                    color=color,
                    verbose=quieter)

        # Define a function that gets called if execution times out. We will
        # raise an exception if the timeout occurs.
        if timeout:
            timed_out = False
            def timeout_function(p):
                nonlocal timed_out
                timed_out = True
                p.kill(group=True)

            # Set the timer to None for now to make sure it's defined.
            timer = None

        starttime = time.time()
        try:
            p = fbuild.subprocess.killableprocess.Popen(cmd,
                stdin=fbuild.subprocess.PIPE if input else stdin,
                stdout=stdout,
                stderr=stderr,
                env=env,
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
            self.logger.log('command failed: ' + cmd_string, color='red')
            raise e from e
        finally:
            if timeout and timer is not None:
                timer.cancel()
        endtime = time.time()

        if returncode:
            self.logger.log(' + ' + cmd_string, verbose=quieter)
        else:
            self.logger.log(' + ' + cmd_string, verbose=1)

        if stdout:
            try:
                self.logger.log(stdout.rstrip().decode(),
                    verbose=stdout_quieter)
            except UnicodeDecodeError:
                self.logger.log(repr(stdout.rstrip()), verbose=stdout_quieter)

        if stderr:
            try:
                self.logger.log(stderr.rstrip().decode(),
                    verbose=stderr_quieter)
            except UnicodeDecodeError:
                self.logger.log(repr(stderr.rstrip()), verbose=stderr_quieter)

        self.logger.log(
            ' - exit %d, %.2f sec' % (returncode, endtime - starttime),
            verbose=2)

        if timeout and timed_out:
            raise fbuild.ExecutionTimedOut(cmd, stdout, stderr, returncode)
        elif returncode:
            raise fbuild.ExecutionError(cmd, stdout, stderr, returncode)

        return stdout, stderr
