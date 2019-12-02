import argparse
import os
import contextlib
import platform
import shutil
import glob

import prepare

to_install = ['cadical', 'glucose30', 'glucose41', 'lingeling', 'maplechrono',
        'maplecm', 'maplesat', 'minicard', 'minisat22', 'minisatgh']

@contextlib.contextmanager
def chdir(newDir):
    oldDir=os.getcwd()
    try:
        os.chdir(newDir)
        yield
    finally:
        os.chdir(oldDir)

def execute(cmd):
    if platform.system()=="Windows":
        cmd="wsl "+ cmd
    print(cmd)

    os.system(cmd)

def main():
    parser=argparse.ArgumentParser(description="Diff Generator",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parms=parser.parse_args()

    shutil.rmtree("build/solvers", ignore_errors=True )

    with chdir("solvers"):
        for solver in to_install:
            with chdir(solver):
                for fileName in glob.glob("*.obj"):
                    os.unlink(fileName)

    shutil.copytree("solvers", "build/solvers")

    for solver in to_install:
        print('preparing {0}'.format(solver))

        with chdir("build"):

            prepare.download_archive(prepare.sources[solver])
            prepare.extract_archive(prepare.sources[solver][-1], solver)
            prepare.adapt_files(solver)

        execute("diff -Naur build/solvers/%s solvers/%s >solvers/patches/%s.patch" % (solver, solver, solver,))



if __name__=="__main__":
    main()