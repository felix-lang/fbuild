import fbuild.builders.c.gcc.darwin as darwin
import fbuild.builders.c.gcc.iphone as iphone

# ------------------------------------------------------------------------------

def static(exe=None, *args, **kwargs):
    if exe is None:
        exe = iphone._iphone_devroot(False) / 'usr/bin/g++'

    return iphone._builder(darwin.static, exe, *args, simulator=False, **kwargs)

def shared(exe=None, *args, **kwargs):
    if exe is None:
        exe = iphone._iphone_devroot(False) / 'usr/bin/g++'

    return iphone._builder(darwin.shared, exe, *args, simulator=False, **kwargs)

# ------------------------------------------------------------------------------

def static_simulator(exe=None, *args, **kwargs):
    if exe is None:
        exe = iphone._iphone_devroot(True) / 'usr/bin/g++'

    return iphone._builder(darwin.static, exe, *args, simulator=True, **kwargs)

def shared_simulator(exe=None, *args, **kwargs):
    if exe is None:
        exe = iphone._iphone_devroot(True) / 'usr/bin/g++'

    return iphone._builder(darwin.shared, exe, *args, simulator=True, **kwargs)
