from setuptools import setup
import sys

sys.path.append('lib')
import fbuild

try:
    import bluesnow
    cmdclass = bluesnow.setuptools_cmdclass
except ImportError:
    cmdclass = {}

data_files = []
if sys.platform.startswith('linux'):
    data_files.append(('/usr/local/share/uprocd/modules', ['misc/fbuild.module']))
    data_files.append(('/usr/share/polkit-1/actions',
                      ['misc/com.github.fbuild.install.policy']))

setup(
    name='fbuild',
    version=fbuild.__version__,
    description='fbuild build system',
    author='Erick Tryzelaar',
    author_email='erickt@felix-lang.org',
    url='https://github.com/felix-lang/fbuild',
    license='BSD',
    packages=[
        'fbuild',
        'fbuild.builders',
        'fbuild.builders.c',
        'fbuild.builders.c.clang',
        'fbuild.builders.c.gcc',
        'fbuild.builders.cxx',
        'fbuild.builders.cxx.clangxx',
        'fbuild.builders.cxx.gxx',
        'fbuild.builders.ocaml',
        'fbuild.config',
        'fbuild.config.c',
        'fbuild.config.cxx',
        'fbuild.db',
        'fbuild.subprocess',
    ],
    entry_points={
        'console_scripts': ['fbuild = fbuild.main:main']
    },
    package_dir={'': 'lib'},
    data_files=data_files,
    cmdclass=cmdclass,
    zip_safe=False,
)
