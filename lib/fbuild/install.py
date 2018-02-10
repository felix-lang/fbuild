import base64
import errno
import os
import pickle
import subprocess
import sys

import fbuild
import fbuild.builders
import fbuild.path
import fbuild.subprocess.killableprocess

# ------------------------------------------------------------------------------


class Commander: pass


class LocalCommander:
    def install(self, file, target, perms=None):
        target.parent.makedirs(exist_ok=True)

        if file.islink():
            # Assume the user knows what they're doing, and just copy the link itself.
            if target.exists():
                target.remove()
            os.symlink(file.readlink(), target)
        else:
            file.copy(target)
        if perms is not None:
            file.chmod(perms)

    def close(self): pass


class PolkitCommander:
    def __init__(self, ctx, proc):
        self.ctx = ctx
        self.proc = proc
        self._send('chdir', os.getcwd())

    def _send(self, *message):
        try:
            encoded = self._encode(message)
            self.proc.stdin.write(encoded)
            self.proc.stdin.write('\n')
            self.proc.stdin.flush()
        except OSError as ex:
            if ex.errno == errno.EPIPE:
                # Broken pipe error...the child process probably died.
                self.close(ask=False)
            raise

    @staticmethod
    def _encode(data):
        return base64.b64encode(pickle.dumps(data)).decode('ascii')

    @staticmethod
    def _decode(data):
        return pickle.loads(base64.b64decode(data.encode('ascii')))

    def install(self, file, target, perms=None):
        self._send('install', file, target, perms)

    def close(self, *, ask=True):
        if ask:
            self._send('close')
        self.proc.wait()

        if self.proc.returncode != 0:
            self.ctx.logger.log("Failed to run 'fbuild install' via pkexec.", color='red')
            sys.exit(self.proc.returncode)


def polkit_process():
    commander = LocalCommander()

    sys.stdout.write('\n')
    sys.stdout.close()
    sys.stdout = sys.stderr

    for line in sys.stdin:
        message = PolkitCommander._decode(line.strip())
        command, args = message[0], message[1:]

        if command == 'chdir':
            os.chdir(args[0])
        elif command == 'install':
            commander.install(*args)
        elif command == 'close':
            sys.exit()


class Installer:
    """An Installer manages installation of all the files marked for installation."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.privileged = False

    def _install(self, commander):
        destdir = self.ctx.install_destdir
        prefix = self.ctx.install_prefix

        for file, subdir, rename, perms in self.ctx.to_install:
            # Generate the full subdirectory.
            if subdir.startswith('/'):
                target_root = fbuild.path.Path(subdir).addroot(destdir)
            else:
                target_root = fbuild.path.Path(subdir).addroot(destdir / prefix)

            # Generate the target path.
            target = target_root / (rename or file.basename())
            file = file.relpath(file.getcwd())

            # Install the file.
            self.ctx.logger.check(' * install', '%s -> %s' % (file, target),
                                  color='yellow')
            commander.install(file, target, perms)

    def _find_pkexec(self):
        try:
            return fbuild.builders.find_program(self.ctx, ['pkexec'], quieter=1)
        except fbuild.builders.MissingProgram:
            return None

    def _load_polkit_process(self, pkexec):
        root_module = fbuild.path.Path(fbuild.__file__)
        root_directory = root_module.parent.parent

        # Make sure Fbuild can be found.
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = '%s:%s' % (root_directory, env['PYTHONPATH'])
        else:
            env['PYTHONPATH'] = root_directory

        # Run the process.
        cmd = [pkexec, sys.executable, '-m', 'fbuild.install', 'polkit']
        proc = fbuild.subprocess.killableprocess.Popen(cmd, stdin=subprocess.PIPE,
                                                       stdout=subprocess.PIPE,
                                                       universal_newlines=True)

        # Make sure it's ready first.
        proc.stdout.readline()
        return proc

    def install(self):
        """Install all the files that are marked for installation. If the user does
        not have permissions to install to the installation prefix, but Polkit's pkexec
        is present, then pkexec will be used to spawn a privileged Fbuild process that
        can install the files."""

        commander = LocalCommander()

        if not self.ctx.install_prefix.access(os.W_OK):
            pkexec = None

            if not self.privileged:
                pkexec = self._find_pkexec()

            if pkexec is None:
                self.ctx.logger.log('Warning: You do not have write access for the ' \
                                    'installation directory.', color='red')
            else:
                proc = self._load_polkit_process(pkexec)
                commander = PolkitCommander(self.ctx, proc)

        try:
            self._install(commander)
        finally:
            commander.close()


if __name__ == '__main__':
    assert sys.argv[1] == 'polkit'
    polkit_process()
