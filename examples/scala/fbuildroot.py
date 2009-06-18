import fbuild.builders.scala

def build():
    scala = fbuild.builders.scala.Builder()

    lib = scala.build_lib('lib.jar', ['world.scala'])

    fbuild.logger.log(' * running script.scala:')
    scala.run_script('script.scala', classpaths=[lib])

    exe = scala.build_lib('exe.jar', ['compiled.scala'], classpaths=[lib])
    fbuild.logger.log(' * running %s:' % exe)
    scala.run_jar('HelloWorld', classpaths=[lib, exe])
