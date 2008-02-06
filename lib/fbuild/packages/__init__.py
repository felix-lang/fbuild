class Package:
    def build(self, conf):
        pass

def build(system, src):
    if isinstance(src, Package):
        return system.future(src.build, system)
    return src
