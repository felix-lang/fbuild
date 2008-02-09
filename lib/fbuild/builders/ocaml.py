#import fbuild.package

# -----------------------------------------------------------------------------

#class Package(fbuild.package.Package):
#    def __init__(self, modules, prefix=None):
#        self.modules = modules
#        self.prefix = prefix
#
#    def build(self, builder):
#        pass

class Builder:
    pass

#def process(package, builder='ocaml_builder', config=None):
#    if config is None:
#        # use the default builder
#        pass
#
#    package.build(getattr(config, builder))

# -----------------------------------------------------------------------------

def config(*args, **kwargs):
    pass
