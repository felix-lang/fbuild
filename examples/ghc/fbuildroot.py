import fbuild
import fbuild.builders.ghc

def build():
    ghc = fbuild.builders.ghc.Builder()

    exe = ghc.build_exe('greet', ['Main.hs'])
    fbuild.execute([exe, 'world!'])
