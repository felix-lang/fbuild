import fbuild.packages

# -----------------------------------------------------------------------------

class Felix(fbuild.packages.SimplePackage):
    default_config = 'fbuild.builders.felix.config'

    def command(self, *args, **kwargs):
        return self.config.compile(*args, **kwargs)
