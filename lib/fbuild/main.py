import os
import sys
import signal
import warnings

# Make sure the current working directory is in the search path so we can find
# the fbuildroot.py.
sys.path.append(os.getcwd())

import fbuild
import fbuild.db
import fbuild.target
import fbuild.path
import fbuild.context
import fbuild.options
import fbuild.builders.file

# If we can't import fbuildroot, save the exception and raise it later.
try:
    import fbuildroot
except ImportError as e:
    fbuildroot = e

# ------------------------------------------------------------------------------

def _call_or_deprecated(current, current_args, deprecated, deprecated_args):
    '''
    Try calling a method on the given fbuildroot. If the method does not exist, then
    try the deprecated version. If the deprecated version exists, then also issue a
    warning.
    '''

    try:
        func = getattr(fbuildroot, current)
    except AttributeError:
        pass
    else:
        return func(*current_args)

    try:
        func = getattr(fbuildroot, deprecated)
    except AttributeError:
        pass
    else:
        warnings.warn('%s is deprecated; use %s instead' % (deprecated, current),
                      DeprecationWarning)
        return func(*deprecated_args)

    return None

def parse_args(argv):
    parser = fbuild.options.make_parser()

    # -------------------------------------------------------------------------
    # Let the fbuildroot modify the argparse parser before parsing.

    parser = _call_or_deprecated(current='arguments', current_args=[parser],
                                 deprecated='pre_options', deprecated_args=[parser]) \
             or parser

    args = parser.parse_args(argv[1:])

    # -------------------------------------------------------------------------
    # Let the fbuildroot modify the argparse parser after parsing.

    args = _call_or_deprecated(current='post_arguments', current_args=[parser, args],
                               deprecated='post_options', deprecated_args=[args]) \
           or args

    return fbuild.context.Context(args)

# ------------------------------------------------------------------------------

def install_files(ctx):
    for subdir, files in ctx.to_install.items():
        # Generate the full subdirectory.
        target_root = fbuild.path.Path(subdir).addroot(ctx.install_prefix)
        for file, froot in files:
            file = file.relpath(file.getcwd())
            # Generate the target path.
            target = file.basename().addroot(target_root / froot)
            # Copy the file.
            ctx.logger.check(' * install', '%s -> %s' % (file, target),
                             color='yellow')
            file.copy(target)

# ------------------------------------------------------------------------------

def build(ctx):
    # Exit early if we're just viewing the state.
    if ctx.options.dump_state:
        # print out the entire state
        ctx.db.dump_database()
        return 0

    # Exit early if we're just deleting a function.
    if ctx.options.delete_function:
        if not ctx.db.delete_function(ctx.options.delete_function):
            raise fbuild.Error('function %r not cached' %
                    ctx.options.delete_function)
        return 0

    # Exit early if we're just deleting a file.
    if ctx.options.delete_file:
        if not ctx.db.delete_file(ctx.options.delete_file):
            raise fbuild.Error('file %r not cached' % ctx.options.delete_file)
        return 0

    # We'll use the arguments as our targets.
    targets = ctx.options.targets

    # Installation stuff.
    if 'install' in targets:
        if targets[-1] != 'install':
            raise fbuild.Error('install must be last target')
        if not set(targets) - {'configure', 'install'}:
            targets.insert(targets.index('install')-1, 'build')

    # Step through each target and execute it.
    for target_name in targets:
        if target_name == 'install':
            install_files(ctx)
        else:
            target = fbuild.target.find(target_name)
            target.function(ctx)

    return 0

# ------------------------------------------------------------------------------

def main(argv=None):
    # Register a couple functions as targets.
    for name in ('configure', 'build'):
        try:
            fbuild.target.register(name=name)(getattr(fbuildroot, name))
        except AttributeError:
            pass

    # --------------------------------------------------------------------------

    # Hacky way of enabling warnings before parsing options.
    if '--no-warnings' not in sys.argv:
        warnings.filterwarnings('always', category=DeprecationWarning)

    # --------------------------------------------------------------------------

    ctx = parse_args(sys.argv if argv is None else argv)

    # --------------------------------------------------------------------------
    # Replace the ctrl-c signal handler with one that will shut down the
    # scheduler before moving on.

    old_handler = signal.getsignal(signal.SIGINT)

    def handle_interrupt(signum, frame):
        ctx.scheduler.shutdown()
        old_handler(signum, frame)

    signal.signal(signal.SIGINT, handle_interrupt)

    # --------------------------------------------------------------------------

    # If we don't wrap this in a try...finally block to shutdown the scheduler
    # after all else finishes, fbuild will hang indefinitely.
    try:
        # If the fbuildroot doesn't exist, error out. We do this now so that
        # there's a chance to ask fbuild for help first.
        if isinstance(fbuildroot, Exception):
            if not os.path.exists('fbuildroot.py'):
                raise fbuild.Error('Cannot find fbuildroot.py')
            else:
                raise fbuildroot

        # Exit early if we want to clean the buildroot.
        if ctx.options.clean_buildroot:
            # Only try to clean the buildroot if it actually exists.
            if ctx.options.buildroot.exists():
                ctx.options.buildroot.rmtree()
            return

        # Prep the context for running.
        ctx.create_buildroot()
        ctx.load_configuration()

        # ... and then run the build.
        try:
            result = build(ctx)
        except fbuild.Error as e:
            ctx.logger.log(e, color='red')
            sys.exit(1)
        except KeyboardInterrupt:
            # It appears that we can't reliably shutdown the scheduler's threads
            # when SIGINT is emitted, because python may raise KeyboardInterrupt
            # between the finally and the mutex.release call.  So, we can find
            # ourselves exiting functions with the lock still held.  This could
            # then cause deadlocks if that lock was ever acquired again.  Oiy.
            print('Interrupted, saving state...')
            raise
        else:
            # Only delete the temporary directory if the build succeeded.
            ctx.clear_temp_dir()
        finally:
            ctx.save_configuration()
            ctx.db.shutdown()
    finally:
        ctx.scheduler.shutdown()

    return result
