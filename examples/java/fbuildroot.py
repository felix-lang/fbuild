import fbuild.builders.java

def build():
    java = fbuild.builders.java.Builder()

    lib = java.build_lib('lib.jar', ['World.java'])
    exe = java.build_lib('exe.jar', ['HelloWorld.java'], classpaths=[lib])
    fbuild.logger.log(' * running %s:' % exe)
    java.run_class('HelloWorld', classpaths=[lib, exe])
