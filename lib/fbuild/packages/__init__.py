from fbuild.system import system

# -----------------------------------------------------------------------------

class Package:
    def build(self):
        pass

def build(src):
    if isinstance(src, Package):
        return system.future(src.build)
    return src
