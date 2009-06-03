import fbuild.builders.scala

def build():
    scala = fbuild.builders.scala.Scala()
    exe = scala.compile('test.scala')
    scala.run(exe, 'HelloWorld')
