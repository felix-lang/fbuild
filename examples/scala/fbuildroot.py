import fbuild.builders.scala

def build():
    scala = fbuild.builders.scala.Builder()

    fbuild.logger.log(' * running script.scala:')
    scala.scala('script.scala')

    lib = scala.build_lib('lib.jar', ['compiled.scala'])
    fbuild.logger.log(' * running %s:' % lib)
    scala.run('HelloWorld', classpaths=[lib])
