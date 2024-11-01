#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## prepare.py
##
##  Created on: Jan 23, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import datetime
import os
import shutil
import sys
import tarfile
import zipfile
import platform

try:  # Python 2
    from urllib import urlopen
except ImportError:  # Python 3
    from urllib.request import urlopen


#
#==============================================================================
sources = {
    'cadical103': (
        'https://github.com/arminbiere/cadical/archive/rel-1.0.3.tar.gz',
        'solvers/cadical103.tar.gz'
    ),
    'cadical153': (
        'https://github.com/arminbiere/cadical/archive/refs/tags/rel-1.5.3.tar.gz',
        'solvers/cadical153.tar.gz'
    ),
    'cadical195': (
        'https://github.com/arminbiere/cadical/archive/refs/tags/rel-1.9.5.tar.gz',
        'solvers/cadical195.tar.gz'
    ),
    'gluecard30': (
        'http://www.labri.fr/perso/lsimon/downloads/softwares/glucose-3.0.tgz',
        'solvers/glucose30.tar.gz'
    ),
    'gluecard41': (
        'http://www.labri.fr/perso/lsimon/downloads/softwares/glucose-syrup-4.1.tgz',
        'solvers/glucose41.tar.gz'
    ),
    'glucose30': (
        'http://www.labri.fr/perso/lsimon/downloads/softwares/glucose-3.0.tgz',
        'solvers/glucose30.tar.gz'
    ),
    'glucose41': (
        'http://www.labri.fr/perso/lsimon/downloads/softwares/glucose-syrup-4.1.tgz',
        'solvers/glucose41.tar.gz'
    ),
    'glucose421': (
        'https://github.com/audemard/glucose/archive/refs/tags/4.2.1.tar.gz',
        'solvers/glucose421.tar.gz'
    ),
    'lingeling': (
        'http://fmv.jku.at/lingeling/lingeling-bbc-9230380-160707-druplig-009.tar.gz',
        'solvers/lingeling.tar.gz'
    ),
    'maplechrono': (
        'http://sat2018.forsyte.tuwien.ac.at/solvers/main_and_glucose_hack/MapleLCMDistChronoBT.zip',
        'solvers/maplechrono.zip'
    ),
    'maplecm': (
        'http://sat2018.forsyte.tuwien.ac.at/solvers/main_and_glucose_hack/Maple_CM.zip',
        'solvers/maplecm.zip'
    ),
    'maplesat': (
        'https://sites.google.com/a/gsd.uwaterloo.ca/maplesat/MapleCOMSPS_pure_LRB.zip',
        'solvers/maplesat.zip'
    ),
    'mergesat3': (
        'https://github.com/conp-solutions/mergesat/archive/refs/tags/v3.0.tar.gz',
        'solvers/mergesat3.tar.gz'
    ),
    'minicard': (
        'https://github.com/liffiton/minicard/archive/v1.2.tar.gz',
        'http://reason.di.fc.ul.pt/~aign/storage/mirror/minicard-v1.2.tar.gz',
        'solvers/minicard.tar.gz'
    ),
    'minisat22': (
        'http://minisat.se/downloads/minisat-2.2.0.tar.gz',
        'solvers/minisat22.tar.gz'
    ),
    'minisatgh': (
        'https://github.com/niklasso/minisat/archive/master.zip',
        'http://reason.di.fc.ul.pt/~aign/storage/mirror/minisatgh-master.zip',
        'solvers/minisatgh.zip'
    ),
    'kissat4': (
        'https://github.com/arminbiere/kissat/archive/refs/tags/rel-4.0.1.tar.gz',   
        'solvers/kissat4.tar.gz'
    )
}

#
#==============================================================================
to_extract = {
    'cadical103': [],
    'cadical153': [],
    'cadical195': [],
    'gluecard30': [],
    'gluecard41': [],
    'glucose30': [],
    'glucose41': [],
    'glucose421': [],
    'lingeling': ['druplig-009.zip', 'lingeling-bbc-9230380-160707.tar.gz'],
    'maplechrono': [],
    'maplecm': [],
    'maplesat': [],
    'mergesat3': [],
    'minicard': [],
    'minisat22': [],
    'minisatgh': [],
    'kissat4': [],
}

#
#==============================================================================
to_move = {
    'cadical103': [
        ('scripts/get-git-id.sh', 'get-git-id.sh'),
        ('scripts/make-build-header.sh', 'make-build-header.sh'),
        ('src/analyze.cpp', 'analyze.cpp'),
        ('src/arena.cpp', 'arena.cpp'),
        ('src/arena.hpp', 'arena.hpp'),
        ('src/assume.cpp', 'assume.cpp'),
        ('src/averages.cpp', 'averages.cpp'),
        ('src/averages.hpp', 'averages.hpp'),
        ('src/backtrack.cpp', 'backtrack.cpp'),
        ('src/backward.cpp', 'backward.cpp'),
        ('src/bins.cpp', 'bins.cpp'),
        ('src/bins.hpp', 'bins.hpp'),
        ('src/block.cpp', 'block.cpp'),
        ('src/block.hpp', 'block.hpp'),
        ('src/cadical.hpp', 'cadical.hpp'),
        ('src/ccadical.cpp', 'ccadical.cpp'),
        ('src/ccadical.h', 'ccadical.h'),
        ('src/checker.cpp', 'checker.cpp'),
        ('src/checker.hpp', 'checker.hpp'),
        ('src/clause.cpp', 'clause.cpp'),
        ('src/clause.hpp', 'clause.hpp'),
        ('src/collect.cpp', 'collect.cpp'),
        ('src/compact.cpp', 'compact.cpp'),
        ('src/config.cpp', 'config.cpp'),
        ('src/config.hpp', 'config.hpp'),
        ('src/contract.hpp', 'contract.hpp'),
        ('src/cover.cpp', 'cover.cpp'),
        ('src/cover.hpp', 'cover.hpp'),
        ('src/decide.cpp', 'decide.cpp'),
        ('src/decompose.cpp', 'decompose.cpp'),
        ('src/deduplicate.cpp', 'deduplicate.cpp'),
        ('src/elim.cpp', 'elim.cpp'),
        ('src/elim.hpp', 'elim.hpp'),
        ('src/ema.cpp', 'ema.cpp'),
        ('src/ema.hpp', 'ema.hpp'),
        ('src/extend.cpp', 'extend.cpp'),
        ('src/external.cpp', 'external.cpp'),
        ('src/external.hpp', 'external.hpp'),
        ('src/file.cpp', 'file0.cpp'),
        ('src/file.hpp', 'file.hpp'),
        ('src/flags.cpp', 'flags.cpp'),
        ('src/flags.hpp', 'flags.hpp'),
        ('src/format.cpp', 'format.cpp'),
        ('src/format.hpp', 'format.hpp'),
        ('src/gates.cpp', 'gates.cpp'),
        ('src/heap.hpp', 'heap.hpp'),
        ('src/instantiate.cpp', 'instantiate.cpp'),
        ('src/instantiate.hpp', 'instantiate.hpp'),
        ('src/internal.cpp', 'internal.cpp'),
        ('src/internal.hpp', 'internal.hpp'),
        ('src/ipasir.cpp', 'ipasir.cpp'),
        ('src/ipasir.h', 'ipasir.h'),
        ('src/level.hpp', 'level.hpp'),
        ('src/limit.cpp', 'limit.cpp'),
        ('src/limit.hpp', 'limit.hpp'),
        ('src/logging.cpp', 'logging.cpp'),
        ('src/logging.hpp', 'logging.hpp'),
        ('src/lucky.cpp', 'lucky.cpp'),
        ('src/mem.hpp', 'mem.hpp'),
        ('src/message.cpp', 'message.cpp'),
        ('src/message.hpp', 'message.hpp'),
        ('src/minimize.cpp', 'minimize.cpp'),
        ('src/mobical.cpp', 'mobical.cpp'),
        ('src/observer.hpp', 'observer.hpp'),
        ('src/occs.cpp', 'occs.cpp'),
        ('src/occs.hpp', 'occs.hpp'),
        ('src/options.cpp', 'options.cpp'),
        ('src/options.hpp', 'options.hpp'),
        ('src/parse.cpp', 'parse.cpp'),
        ('src/parse.hpp', 'parse.hpp'),
        ('src/phases.cpp', 'phases.cpp'),
        ('src/phases.hpp', 'phases.hpp'),
        ('src/probe.cpp', 'probe.cpp'),
        ('src/profile.cpp', 'profile.cpp'),
        ('src/profile.hpp', 'profile.hpp'),
        ('src/proof.cpp', 'proof.cpp'),
        ('src/proof.hpp', 'proof.hpp'),
        ('src/propagate.cpp', 'propagate.cpp'),
        ('src/queue.cpp', 'queue.cpp'),
        ('src/queue.hpp', 'queue.hpp'),
        ('src/radix.hpp', 'radix.hpp'),
        ('src/random.cpp', 'random.cpp'),
        ('src/random.hpp', 'random.hpp'),
        ('src/reduce.cpp', 'reduce.cpp'),
        ('src/reluctant.hpp', 'reluctant.hpp'),
        ('src/rephase.cpp', 'rephase.cpp'),
        ('src/report.cpp', 'report.cpp'),
        ('src/resources.cpp', 'resources.cpp'),
        ('src/resources.hpp', 'resources.hpp'),
        ('src/restart.cpp', 'restart.cpp'),
        ('src/restore.cpp', 'restore.cpp'),
        ('src/score.cpp', 'score.cpp'),
        ('src/score.hpp', 'score.hpp'),
        ('src/signal.cpp', 'signal.cpp'),
        ('src/signal.hpp', 'signal.hpp'),
        ('src/solution.cpp', 'solution.cpp'),
        ('src/solver.cpp', 'solver.cpp'),
        ('src/stats.cpp', 'stats.cpp'),
        ('src/stats.hpp', 'stats.hpp'),
        ('src/subsume.cpp', 'subsume.cpp'),
        ('src/terminal.cpp', 'terminal.cpp'),
        ('src/terminal.hpp', 'terminal.hpp'),
        ('src/ternary.cpp', 'ternary.cpp'),
        ('src/tracer.cpp', 'tracer.cpp'),
        ('src/tracer.hpp', 'tracer.hpp'),
        ('src/transred.cpp', 'transred.cpp'),
        ('src/util.cpp', 'util.cpp'),
        ('src/util.hpp', 'util.hpp'),
        ('src/var.cpp', 'var.cpp'),
        ('src/var.hpp', 'var.hpp'),
        ('src/version.cpp', 'version.cpp'),
        ('src/version.hpp', 'version.hpp'),
        ('src/vivify.cpp', 'vivify.cpp'),
        ('src/vivify.hpp', 'vivify.hpp'),
        ('src/walk.cpp', 'walk.cpp'),
        ('src/watch.cpp', 'watch.cpp'),
        ('src/watch.hpp', 'watch.hpp'),
        ('VERSION', 'VERSION.txt')
    ],
    'cadical153': [
        ('scripts/get-git-id.sh', 'get-git-id.sh'),
        ('scripts/make-build-header.sh', 'make-build-header.sh'),
        ('src/analyze.cpp', 'analyze.cpp'),
        ('src/arena.cpp', 'arena.cpp'),
        ('src/arena.hpp', 'arena.hpp'),
        ('src/assume.cpp', 'assume.cpp'),
        ('src/averages.cpp', 'averages.cpp'),
        ('src/averages.hpp', 'averages.hpp'),
        ('src/backtrack.cpp', 'backtrack.cpp'),
        ('src/backward.cpp', 'backward.cpp'),
        ('src/bins.cpp', 'bins.cpp'),
        ('src/bins.hpp', 'bins.hpp'),
        ('src/block.cpp', 'block.cpp'),
        ('src/block.hpp', 'block.hpp'),
        ('src/cadical.hpp', 'cadical.hpp'),
        ('src/checker.cpp', 'checker.cpp'),
        ('src/checker.hpp', 'checker.hpp'),
        ('src/clause.cpp', 'clause.cpp'),
        ('src/clause.hpp', 'clause.hpp'),
        ('src/collect.cpp', 'collect.cpp'),
        ('src/compact.cpp', 'compact.cpp'),
        ('src/condition.cpp', 'condition.cpp'),
        ('src/config.cpp', 'config.cpp'),
        ('src/config.hpp', 'config.hpp'),
        ('src/constrain.cpp', 'constrain.cpp'),
        ('src/contract.cpp', 'contract.cpp'),
        ('src/contract.hpp', 'contract.hpp'),
        ('src/cover.cpp', 'cover.cpp'),
        ('src/cover.hpp', 'cover.hpp'),
        ('src/decide.cpp', 'decide.cpp'),
        ('src/decompose.cpp', 'decompose.cpp'),
        ('src/deduplicate.cpp', 'deduplicate.cpp'),
        ('src/elim.cpp', 'elim.cpp'),
        ('src/elim.hpp', 'elim.hpp'),
        ('src/ema.cpp', 'ema.cpp'),
        ('src/ema.hpp', 'ema.hpp'),
        ('src/extend.cpp', 'extend.cpp'),
        ('src/external.cpp', 'external.cpp'),
        ('src/external.hpp', 'external.hpp'),
        ('src/file.cpp', 'file0.cpp'),
        ('src/file.hpp', 'file.hpp'),
        ('src/flags.cpp', 'flags.cpp'),
        ('src/flags.hpp', 'flags.hpp'),
        ('src/format.cpp', 'format.cpp'),
        ('src/format.hpp', 'format.hpp'),
        ('src/gates.cpp', 'gates.cpp'),
        ('src/heap.hpp', 'heap.hpp'),
        ('src/instantiate.cpp', 'instantiate.cpp'),
        ('src/instantiate.hpp', 'instantiate.hpp'),
        ('src/internal.cpp', 'internal.cpp'),
        ('src/internal.hpp', 'internal.hpp'),
        ('src/inttypes.hpp', 'inttypes.hpp'),
        ('src/level.hpp', 'level.hpp'),
        ('src/limit.cpp', 'limit.cpp'),
        ('src/limit.hpp', 'limit.hpp'),
        ('src/logging.cpp', 'logging.cpp'),
        ('src/logging.hpp', 'logging.hpp'),
        ('src/lookahead.cpp', 'lookahead.cpp'),
        ('src/lucky.cpp', 'lucky.cpp'),
        ('src/message.cpp', 'message.cpp'),
        ('src/message.hpp', 'message.hpp'),
        ('src/minimize.cpp', 'minimize.cpp'),
        ('src/mobical.cpp', 'mobical.cpp'),
        ('src/observer.hpp', 'observer.hpp'),
        ('src/occs.cpp', 'occs.cpp'),
        ('src/occs.hpp', 'occs.hpp'),
        ('src/options.cpp', 'options.cpp'),
        ('src/options.hpp', 'options.hpp'),
        ('src/parse.cpp', 'parse.cpp'),
        ('src/parse.hpp', 'parse.hpp'),
        ('src/phases.cpp', 'phases.cpp'),
        ('src/phases.hpp', 'phases.hpp'),
        ('src/probe.cpp', 'probe.cpp'),
        ('src/profile.cpp', 'profile.cpp'),
        ('src/profile.hpp', 'profile.hpp'),
        ('src/proof.cpp', 'proof.cpp'),
        ('src/proof.hpp', 'proof.hpp'),
        ('src/propagate.cpp', 'propagate.cpp'),
        ('src/queue.cpp', 'queue.cpp'),
        ('src/queue.hpp', 'queue.hpp'),
        ('src/radix.hpp', 'radix.hpp'),
        ('src/random.cpp', 'random.cpp'),
        ('src/random.hpp', 'random.hpp'),
        ('src/range.hpp', 'range.hpp'),
        ('src/reap.cpp', 'reap.cpp'),
        ('src/reap.hpp', 'reap.hpp'),
        ('src/reduce.cpp', 'reduce.cpp'),
        ('src/reluctant.hpp', 'reluctant.hpp'),
        ('src/rephase.cpp', 'rephase.cpp'),
        ('src/report.cpp', 'report.cpp'),
        ('src/resources.cpp', 'resources.cpp'),
        ('src/resources.hpp', 'resources.hpp'),
        ('src/restart.cpp', 'restart.cpp'),
        ('src/restore.cpp', 'restore.cpp'),
        ('src/score.cpp', 'score.cpp'),
        ('src/score.hpp', 'score.hpp'),
        ('src/shrink.cpp', 'shrink.cpp'),
        ('src/signal.cpp', 'signal.cpp'),
        ('src/signal.hpp', 'signal.hpp'),
        ('src/solution.cpp', 'solution.cpp'),
        ('src/solver.cpp', 'solver.cpp'),
        ('src/stats.cpp', 'stats.cpp'),
        ('src/stats.hpp', 'stats.hpp'),
        ('src/subsume.cpp', 'subsume.cpp'),
        ('src/terminal.cpp', 'terminal.cpp'),
        ('src/terminal.hpp', 'terminal.hpp'),
        ('src/ternary.cpp', 'ternary.cpp'),
        ('src/tracer.cpp', 'tracer.cpp'),
        ('src/tracer.hpp', 'tracer.hpp'),
        ('src/transred.cpp', 'transred.cpp'),
        ('src/util.cpp', 'util.cpp'),
        ('src/util.hpp', 'util.hpp'),
        ('src/var.cpp', 'var.cpp'),
        ('src/var.hpp', 'var.hpp'),
        ('src/version.cpp', 'version.cpp'),
        ('src/version.hpp', 'version.hpp'),
        ('src/vivify.cpp', 'vivify.cpp'),
        ('src/vivify.hpp', 'vivify.hpp'),
        ('src/walk.cpp', 'walk.cpp'),
        ('src/watch.cpp', 'watch.cpp'),
        ('src/watch.hpp', 'watch.hpp'),
        ('VERSION', 'VERSION.txt')
    ],
    'cadical195': [
        ('scripts/get-git-id.sh', 'get-git-id.sh'),
        ('scripts/make-build-header.sh', 'make-build-header.sh'),
        ('src/analyze.cpp', 'analyze.cpp'),
        ('src/arena.cpp', 'arena.cpp'),
        ('src/arena.hpp', 'arena.hpp'),
        ('src/assume.cpp', 'assume.cpp'),
        ('src/averages.cpp', 'averages.cpp'),
        ('src/averages.hpp', 'averages.hpp'),
        ('src/backtrack.cpp', 'backtrack.cpp'),
        ('src/backward.cpp', 'backward.cpp'),
        ('src/bins.cpp', 'bins.cpp'),
        ('src/bins.hpp', 'bins.hpp'),
        ('src/block.cpp', 'block.cpp'),
        ('src/block.hpp', 'block.hpp'),
        ('src/cadical.hpp', 'cadical.hpp'),
        ('src/checker.cpp', 'checker.cpp'),
        ('src/checker.hpp', 'checker.hpp'),
        ('src/clause.cpp', 'clause.cpp'),
        ('src/clause.hpp', 'clause.hpp'),
        ('src/collect.cpp', 'collect.cpp'),
        ('src/compact.cpp', 'compact.cpp'),
        ('src/condition.cpp', 'condition.cpp'),
        ('src/config.cpp', 'config.cpp'),
        ('src/config.hpp', 'config.hpp'),
        ('src/constrain.cpp', 'constrain.cpp'),
        ('src/contract.cpp', 'contract.cpp'),
        ('src/contract.hpp', 'contract.hpp'),
        ('src/cover.cpp', 'cover.cpp'),
        ('src/cover.hpp', 'cover.hpp'),
        ('src/decide.cpp', 'decide.cpp'),
        ('src/decompose.cpp', 'decompose.cpp'),
        ('src/decompose.hpp', 'decompose.hpp'),
        ('src/deduplicate.cpp', 'deduplicate.cpp'),
        ('src/drattracer.cpp', 'drattracer.cpp'),
        ('src/drattracer.hpp', 'drattracer.hpp'),
        ('src/elim.cpp', 'elim.cpp'),
        ('src/elim.hpp', 'elim.hpp'),
        ('src/ema.cpp', 'ema.cpp'),
        ('src/ema.hpp', 'ema.hpp'),
        ('src/extend.cpp', 'extend.cpp'),
        ('src/external.cpp', 'external.cpp'),
        ('src/external.hpp', 'external.hpp'),
        ('src/external_propagate.cpp', 'external_propagate.cpp'),
        ('src/file.cpp', 'file0.cpp'),
        ('src/file.hpp', 'file.hpp'),
        ('src/flags.cpp', 'flags.cpp'),
        ('src/flags.hpp', 'flags.hpp'),
        ('src/flip.cpp', 'flip.cpp'),
        ('src/format.cpp', 'format.cpp'),
        ('src/format.hpp', 'format.hpp'),
        ('src/frattracer.cpp', 'frattracer.cpp'),
        ('src/frattracer.hpp', 'frattracer.hpp'),
        ('src/gates.cpp', 'gates.cpp'),
        ('src/heap.hpp', 'heap.hpp'),
        ('src/idruptracer.cpp', 'idruptracer.cpp'),
        ('src/idruptracer.hpp', 'idruptracer.hpp'),
        ('src/instantiate.cpp', 'instantiate.cpp'),
        ('src/instantiate.hpp', 'instantiate.hpp'),
        ('src/internal.cpp', 'internal.cpp'),
        ('src/internal.hpp', 'internal.hpp'),
        ('src/inttypes.hpp', 'inttypes.hpp'),
        ('src/level.hpp', 'level.hpp'),
        ('src/limit.cpp', 'limit.cpp'),
        ('src/limit.hpp', 'limit.hpp'),
        ('src/logging.cpp', 'logging.cpp'),
        ('src/logging.hpp', 'logging.hpp'),
        ('src/lookahead.cpp', 'lookahead.cpp'),
        ('src/lratbuilder.cpp', 'lratbuilder.cpp'),
        ('src/lratbuilder.hpp', 'lratbuilder.hpp'),
        ('src/lratchecker.cpp', 'lratchecker.cpp'),
        ('src/lratchecker.hpp', 'lratchecker.hpp'),
        ('src/lrattracer.cpp', 'lrattracer.cpp'),
        ('src/lrattracer.hpp', 'lrattracer.hpp'),
        ('src/lucky.cpp', 'lucky.cpp'),
        ('src/message.cpp', 'message.cpp'),
        ('src/message.hpp', 'message.hpp'),
        ('src/minimize.cpp', 'minimize.cpp'),
        ('src/mobical.cpp', 'mobical.cpp'),
        ('src/occs.cpp', 'occs.cpp'),
        ('src/occs.hpp', 'occs.hpp'),
        ('src/options.cpp', 'options.cpp'),
        ('src/options.hpp', 'options.hpp'),
        ('src/parse.cpp', 'parse.cpp'),
        ('src/parse.hpp', 'parse.hpp'),
        ('src/phases.cpp', 'phases.cpp'),
        ('src/phases.hpp', 'phases.hpp'),
        ('src/probe.cpp', 'probe.cpp'),
        ('src/profile.cpp', 'profile.cpp'),
        ('src/profile.hpp', 'profile.hpp'),
        ('src/proof.cpp', 'proof.cpp'),
        ('src/proof.hpp', 'proof.hpp'),
        ('src/propagate.cpp', 'propagate.cpp'),
        ('src/queue.cpp', 'queue.cpp'),
        ('src/queue.hpp', 'queue.hpp'),
        ('src/radix.hpp', 'radix.hpp'),
        ('src/random.cpp', 'random.cpp'),
        ('src/random.hpp', 'random.hpp'),
        ('src/range.hpp', 'range.hpp'),
        ('src/reap.cpp', 'reap.cpp'),
        ('src/reap.hpp', 'reap.hpp'),
        ('src/reduce.cpp', 'reduce.cpp'),
        ('src/reluctant.hpp', 'reluctant.hpp'),
        ('src/rephase.cpp', 'rephase.cpp'),
        ('src/report.cpp', 'report.cpp'),
        ('src/resources.cpp', 'resources.cpp'),
        ('src/resources.hpp', 'resources.hpp'),
        ('src/restart.cpp', 'restart.cpp'),
        ('src/restore.cpp', 'restore.cpp'),
        ('src/score.cpp', 'score.cpp'),
        ('src/score.hpp', 'score.hpp'),
        ('src/shrink.cpp', 'shrink.cpp'),
        ('src/signal.cpp', 'signal.cpp'),
        ('src/signal.hpp', 'signal.hpp'),
        ('src/solution.cpp', 'solution.cpp'),
        ('src/solver.cpp', 'solver.cpp'),
        ('src/stats.cpp', 'stats.cpp'),
        ('src/stats.hpp', 'stats.hpp'),
        ('src/subsume.cpp', 'subsume.cpp'),
        ('src/terminal.cpp', 'terminal.cpp'),
        ('src/terminal.hpp', 'terminal.hpp'),
        ('src/ternary.cpp', 'ternary.cpp'),
        ('src/tracer.hpp', 'tracer.hpp'),
        ('src/transred.cpp', 'transred.cpp'),
        ('src/util.cpp', 'util.cpp'),
        ('src/util.hpp', 'util.hpp'),
        ('src/var.cpp', 'var.cpp'),
        ('src/var.hpp', 'var.hpp'),
        ('src/veripbtracer.cpp', 'veripbtracer.cpp'),
        ('src/veripbtracer.hpp', 'veripbtracer.hpp'),
        ('src/version.cpp', 'version.cpp'),
        ('src/version.hpp', 'version.hpp'),
        ('src/vivify.cpp', 'vivify.cpp'),
        ('src/vivify.hpp', 'vivify.hpp'),
        ('src/walk.cpp', 'walk.cpp'),
        ('src/watch.cpp', 'watch.cpp'),
        ('src/watch.hpp', 'watch.hpp'),
        ('VERSION', 'VERSION.txt')
    ],
    'gluecard30': [],
    'gluecard41': [],
    'glucose30': [],
    'glucose41': [],
    'glucose421': [],
    'lingeling': [
        ('druplig-009/druplig.c', 'druplig.c'),
        ('druplig-009/druplig.h', 'druplig.h'),
        ('lingeling-bbc-9230380-160707/lglconst.h', 'lglconst.h'),
        ('lingeling-bbc-9230380-160707/lglib.c', 'lglib.c'),
        ('lingeling-bbc-9230380-160707/lglib.h', 'lglib.h'),
        ('lingeling-bbc-9230380-160707/lgloptl.h', 'lgloptl.h'),
        ('lingeling-bbc-9230380-160707/lglopts.c', 'lglopts.c'),
        ('lingeling-bbc-9230380-160707/lglopts.h', 'lglopts.h')
    ],
    'maplechrono': [
        ('sources/core', 'core'),
        ('sources/mtl', 'mtl'),
        ('sources/utils', 'utils')
    ],
    'maplecm': [
        ('sources/core', 'core'),
        ('sources/mtl', 'mtl'),
        ('sources/utils', 'utils')
    ],
    'maplesat': [],
    'mergesat3': [
        ('minisat/core', 'core'),
        ('minisat/mtl', 'mtl'),
        ('minisat/simp', 'simp'),
        ('minisat/utils', 'utils')
    ],
    'minicard': [
        ('core', '_core'),
        ('minicard', 'core')
    ],
    'minisat22': [],
    'minisatgh': [
        ('minisat/core', 'core'),
        ('minisat/mtl', 'mtl'),
        ('minisat/utils', 'utils')
    ],
    'kissat4': [
        ('VERSION', 'VERSION.txt'),
        ('scripts/generate-build-header.sh', 'generate-build-header.sh'),
        ('src/allocate.c','allocate.cc'),
        ('src/allocate.h','allocate.hh'),
        ('src/analyze.c','analyze.cc'),
        ('src/analyze.h','analyze.hh'),
        ('src/ands.c','ands.cc'),
        ('src/ands.h','ands.hh'),
        ('src/application.c','application.cc'),
        ('src/application.h','application.hh'),
        ('src/arena.c','arena.cc'),
        ('src/arena.h','arena.hh'),
        ('src/array.h','array.hh'),
        ('src/assign.c','assign.cc'),
        ('src/assign.h','assign.hh'),
        ('src/attribute.h','attribute.hh'),
        ('src/averages.c','averages.cc'),
        ('src/averages.h','averages.hh'),
        ('src/backbone.c','backbone.cc'),
        ('src/backbone.h','backbone.hh'),
        ('src/backtrack.c','backtrack.cc'),
        ('src/backtrack.h','backtrack.hh'),
        ('src/build.c','build.cc'),
        ('src/bump.c','bump.cc'),
        ('src/bump.h','bump.hh'),
        ('src/check.c','check.cc'),
        ('src/check.h','check.hh'),
        ('src/classify.c','classify.cc'),
        ('src/classify.h','classify.hh'),
        ('src/clause.c','clause.cc'),
        ('src/clause.h','clause.hh'),
        ('src/collect.c','collect.cc'),
        ('src/collect.h','collect.hh'),
        ('src/colors.c','colors.cc'),
        ('src/colors.h','colors.hh'),
        ('src/compact.c','compact.cc'),
        ('src/compact.h','compact.hh'),
        ('src/config.c','config.cc'),
        ('src/config.h','config.hh'),
        ('src/congruence.c','congruence.cc'),
        ('src/congruence.h','congruence.hh'),
        ('src/cover.h','cover.hh'),
        ('src/decide.c','decide.cc'),
        ('src/decide.h','decide.hh'),
        ('src/deduce.c','deduce.cc'),
        ('src/deduce.h','deduce.hh'),
        ('src/definition.c','definition.cc'),
        ('src/definition.h','definition.hh'),
        ('src/dense.c','dense.cc'),
        ('src/dense.h','dense.hh'),
        ('src/dump.c','dump.cc'),
        ('src/eliminate.c','eliminate.cc'),
        ('src/eliminate.h','eliminate.hh'),
        ('src/equivalences.c','equivalences.cc'),
        ('src/equivalences.h','equivalences.hh'),
        ('src/error.c','error.cc'),
        ('src/error.h','error.hh'),
        ('src/extend.c','extend.cc'),
        ('src/extend.h','extend.hh'),
        ('src/factor.c','factor.cc'),
        ('src/factor.h','factor.hh'),
        ('src/fastassign.h','fastassign.hh'),
        ('src/fastel.c','fastel.cc'),
        ('src/fastel.h','fastel.hh'),
        ('src/fifo.h','fifo.hh'),
        ('src/file.c','file.cc'),
        ('src/file.h','file.hh'),
        ('src/flags.c','flags.cc'),
        ('src/flags.h','flags.hh'),
        ('src/format.c','format.cc'),
        ('src/format.h','format.hh'),
        ('src/forward.c','forward.cc'),
        ('src/forward.h','forward.hh'),
        ('src/frames.h','frames.hh'),
        ('src/gates.c','gates.cc'),
        ('src/gates.h','gates.hh'),
        ('src/handle.c','handle.cc'),
        ('src/handle.h','handle.hh'),
        ('src/heap.c','heap.cc'),
        ('src/heap.h','heap.hh'),
        ('src/ifthenelse.c','ifthenelse.cc'),
        ('src/ifthenelse.h','ifthenelse.hh'),
        ('src/import.c','import.cc'),
        ('src/import.h','import.hh'),
        ('src/inline.h','inline.hh'),
        ('src/inlineassign.h','inlineassign.hh'),
        ('src/inlineframes.h','inlineframes.hh'),
        ('src/inlineheap.h','inlineheap.hh'),
        ('src/inlinequeue.h','inlinequeue.hh'),
        ('src/inlinevector.h','inlinevector.hh'),
        ('src/internal.c','internal.cc'),
        ('src/internal.h','internal.hh'),
        ('src/keatures.h','keatures.hh'),
        ('src/kimits.c','kimits.cc'),
        ('src/kimits.h','kimits.hh'),
        ('src/kissat.h','kissat.hh'),
        ('src/kitten.c','kitten.cc'),
        ('src/kitten.h','kitten.hh'),
        ('src/krite.c','krite.cc'),
        ('src/krite.h','krite.hh'),
        ('src/learn.c','learn.cc'),
        ('src/learn.h','learn.hh'),
        ('src/literal.h','literal.hh'),
        ('src/logging.c','logging.cc'),
        ('src/logging.h','logging.hh'),
        ('src/lucky.c','lucky.cc'),
        ('src/lucky.h','lucky.hh'),
        ('src/main.c','main.cc'),
        ('src/minimize.c','minimize.cc'),
        ('src/minimize.h','minimize.hh'),
        ('src/mode.c','mode.cc'),
        ('src/mode.h','mode.hh'),
        ('src/options.c','options.cc'),
        ('src/options.h','options.hh'),
        ('src/parse.c','parse.cc'),
        ('src/parse.h','parse.hh'),
        ('src/phases.c','phases.cc'),
        ('src/phases.h','phases.hh'),
        ('src/preprocess.c','preprocess.cc'),
        ('src/preprocess.h','preprocess.hh'),
        ('src/print.c','print.cc'),
        ('src/print.h','print.hh'),
        ('src/probe.c','probe.cc'),
        ('src/probe.h','probe.hh'),
        ('src/profile.c','profile.cc'),
        ('src/profile.h','profile.hh'),
        ('src/promote.c','promote.cc'),
        ('src/promote.h','promote.hh'),
        ('src/proof.c','proof.cc'),
        ('src/proof.h','proof.hh'),
        ('src/propbeyond.c','propbeyond.cc'),
        ('src/propbeyond.h','propbeyond.hh'),
        ('src/propdense.c','propdense.cc'),
        ('src/propdense.h','propdense.hh'),
        ('src/propinitially.c','propinitially.cc'),
        ('src/propinitially.h','propinitially.hh'),
        ('src/proplit.h','proplit.hh'),
        ('src/proprobe.c','proprobe.cc'),
        ('src/proprobe.h','proprobe.hh'),
        ('src/propsearch.c','propsearch.cc'),
        ('src/propsearch.h','propsearch.hh'),
        ('src/queue.c','queue.cc'),
        ('src/queue.h','queue.hh'),
        ('src/random.h','random.hh'),
        ('src/rank.h','rank.hh'),
        ('src/reduce.c','reduce.cc'),
        ('src/reduce.h','reduce.hh'),
        ('src/reference.h','reference.hh'),
        ('src/reluctant.c','reluctant.cc'),
        ('src/reluctant.h','reluctant.hh'),
        ('src/reorder.c','reorder.cc'),
        ('src/reorder.h','reorder.hh'),
        ('src/rephase.c','rephase.cc'),
        ('src/rephase.h','rephase.hh'),
        ('src/report.c','report.cc'),
        ('src/report.h','report.hh'),
        ('src/require.h','require.hh'),
        ('src/resize.c','resize.cc'),
        ('src/resize.h','resize.hh'),
        ('src/resolve.c','resolve.cc'),
        ('src/resolve.h','resolve.hh'),
        ('src/resources.c','resources.cc'),
        ('src/resources.h','resources.hh'),
        ('src/restart.c','restart.cc'),
        ('src/restart.h','restart.hh'),
        ('src/search.c','search.cc'),
        ('src/search.h','search.hh'),
        ('src/shrink.c','shrink.cc'),
        ('src/shrink.h','shrink.hh'),
        ('src/smooth.c','smooth.cc'),
        ('src/smooth.h','smooth.hh'),
        ('src/sort.c','sort.cc'),
        ('src/sort.h','sort.hh'),
        ('src/stack.c','stack.cc'),
        ('src/stack.h','stack.hh'),
        ('src/statistics.c','statistics.cc'),
        ('src/statistics.h','statistics.hh'),
        ('src/strengthen.c','strengthen.cc'),
        ('src/strengthen.h','strengthen.hh'),
        ('src/substitute.c','substitute.cc'),
        ('src/substitute.h','substitute.hh'),
        ('src/sweep.c','sweep.cc'),
        ('src/sweep.h','sweep.hh'),
        ('src/terminate.c','terminate.cc'),
        ('src/terminate.h','terminate.hh'),
        ('src/tiers.c','tiers.cc'),
        ('src/tiers.h','tiers.hh'),
        ('src/trail.c','trail.cc'),
        ('src/trail.h','trail.hh'),
        ('src/transitive.c','transitive.cc'),
        ('src/transitive.h','transitive.hh'),
        ('src/utilities.c','utilities.cc'),
        ('src/utilities.h','utilities.hh'),
        ('src/value.h','value.hh'),
        ('src/vector.c','vector.cc'),
        ('src/vector.h','vector.hh'),
        ('src/vivify.c','vivify.cc'),
        ('src/vivify.h','vivify.hh'),
        ('src/walk.c','walk.cc'),
        ('src/walk.h','walk.hh'),
        ('src/warmup.c','warmup.cc'),
        ('src/warmup.h','warmup.hh'),
        ('src/watch.c','watch.cc'),
        ('src/watch.h','watch.hh'),
        ('src/weaken.c','weaken.cc'),
        ('src/weaken.h','weaken.hh'),
        ('src/witness.c','witness.cc'),
        ('src/witness.h','witness.hh'),
    ]
}

#
#==============================================================================
to_remove = {
    'cadical103': [
        '.gitignore',
        '.travis.yml',
        'BUILD.md',
        'CONTRIBUTING',
        'LICENSE',
        'makefile.in',
        'README.md',
        'configure',
        'scripts',
        'src',
        'test',
        'mobical.cpp'
    ],
    'cadical153': [
        '.gitignore',
        '.travis.yml',
        'BUILD.md',
        'CONTRIBUTING',
        'LICENSE',
        'makefile.in',
        'README.md',
        'configure',
        'scripts',
        'src',
        'test',
        'mobical.cpp'
    ],
    'cadical195': [
        '.gitignore',
        'BUILD.md',
        'CONTRIBUTING.md',
        'LICENSE',
        'makefile.in',
        'README.md',
        'configure',
        'scripts',
        'src',
        'test',
        'mobical.cpp'
    ],
    'gluecard30': [
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'utils/Makefile'
    ],
    'gluecard41': [
        '._Changelog',
        '._LICENCE',
        '._README',
        '._core',
        '._mtl',
        '._parallel',
        '._simp',
        '._utils',
        'Changelog',
        'core/._BoundedQueue.h',
        'core/._Constants.h',
        'core/._Dimacs.h',
        'core/._Makefile',
        'core/._Solver.cc',
        'core/._Solver.h',
        'core/._SolverStats.h',
        'core/._SolverTypes.h',
        'core/Dimacs.h',
        'core/Makefile',
        'LICENCE',
        'README',
        'mtl/._Alg.h',
        'mtl/._Alloc.h',
        'mtl/._Clone.h',
        'mtl/._Heap.h',
        'mtl/._IntTypes.h',
        'mtl/._Map.h',
        'mtl/._Queue.h',
        'mtl/._Sort.h',
        'mtl/._Vec.h',
        'mtl/._VecThreads.h',
        'mtl/._XAlloc.h',
        'mtl/._config.mk',
        'mtl/._template.mk',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'parallel',
        'utils/._Makefile',
        'utils/._Options.cc',
        'utils/._Options.h',
        'utils/._ParseUtils.h',
        'utils/._System.cc',
        'utils/._System.h',
        'utils/Makefile'
    ],
    'glucose30': [
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'utils/Makefile'
    ],
    'glucose41': [
        '._Changelog',
        '._LICENCE',
        '._README',
        '._core',
        '._mtl',
        '._parallel',
        '._simp',
        '._utils',
        'Changelog',
        'core/._BoundedQueue.h',
        'core/._Constants.h',
        'core/._Dimacs.h',
        'core/._Makefile',
        'core/._Solver.cc',
        'core/._Solver.h',
        'core/._SolverStats.h',
        'core/._SolverTypes.h',
        'core/Dimacs.h',
        'core/Makefile',
        'LICENCE',
        'README',
        'mtl/._Alg.h',
        'mtl/._Alloc.h',
        'mtl/._Clone.h',
        'mtl/._Heap.h',
        'mtl/._IntTypes.h',
        'mtl/._Map.h',
        'mtl/._Queue.h',
        'mtl/._Sort.h',
        'mtl/._Vec.h',
        'mtl/._VecThreads.h',
        'mtl/._XAlloc.h',
        'mtl/._config.mk',
        'mtl/._template.mk',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'parallel',
        'utils/._Makefile',
        'utils/._Options.cc',
        'utils/._Options.h',
        'utils/._ParseUtils.h',
        'utils/._System.cc',
        'utils/._System.h',
        'utils/Makefile'
    ],
    'glucose421': [
        'CHANGELOG',
        'CMakeLists.txt',
        '.gitignore',
        'LICENSE',
        'README.md',
        'simp',
        'parallel',
        'mtl/template.mk',
        'mtl/config.mk',
        'core/Dimacs.h',
        'core/Makefile',
        'utils/Makefile'
    ],
    'lingeling': [
        'druplig-009',
        'druplig-009.zip',
        'lingeling-bbc-9230380-160707',
        'lingeling-bbc-9230380-160707.tar.gz',
        'extract-and-compile.sh',
        '.tar.gz',
        'README'
    ],
    'maplechrono': [
        'bin',
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'mtl/config.mk',
        'mtl/template.mk',
        'utils/Makefile',
        'sources',
        'starexec_build'
    ],
    'maplecm': [
        '__MACOSX',
        'bin',
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'mtl/config.mk',
        'mtl/template.mk',
        'utils/Makefile',
        'utils/Options.o',
        'utils/System.o',
        'sources',
        'starexec_build'
    ],
    'maplesat': [
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'doc',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'utils/Makefile',
        'LICENSE',
        'README'
    ],
    'mergesat3': [
        '.clang-format',
        '.github',
        '.travis.yml',
        'core/Makefile',
        'core/ipasir.h',
        'doc',
        'LICENSE',
        'licence.txt',
        'Makefile',
        'minisat',
        'mtl/config.mk',
        'mtl/template.mk',
        'README',
        'simp',
        'tools',
        'utils/Makefile',
        '.gitignore'
    ],
    'minicard': [
        '_core',
        'encodings',
        'minicard_encodings',
        'minicard_simp_encodings',
        'tests',
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'core/opb.h',
        'mtl/config.mk',
        'mtl/template.mk',
        'utils/Makefile',
        'LICENSE',
        'README',
        '.gitignore'
    ],
    'minisat22': [
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'doc',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'utils/Makefile',
        'LICENSE',
        'README'
    ],
    'minisatgh': [
        'core/Dimacs.h',
        'core/Main.cc',
        'doc',
        'minisat',
        'CMakeLists.txt',
        'LICENSE',
        'Makefile',
        'README',
        '.gitignore'
    ],
    'kissat4': [
        'makefile.in',
        'configure',
        'src/configure',
        'scripts',
        'test',
        'README.md',
        'LICENSE',
        'NEWS.md',
        'CONTRIBUTING',
        '.clang-format',
        '.gitignore'
    ]
}


#
#==============================================================================
def do(to_install):
    """
        Prepare all solvers specified in the command line.
    """

    for solver in to_install:
        print('preparing {0}'.format(solver))

        download_archive(sources[solver])
        extract_archive(sources[solver][-1], solver)
        adapt_files(solver)
        patch_solver(solver)

        if platform.system() != 'Windows':
            compile_solver(solver)

#
#==============================================================================
def download_archive(sources):
    """
        Downloads an archive and saves locally (taken from PySMT).
    """

    # last element is expected to be the local archive name
    save_to = sources[-1]

    # not downloading the file again if it exists
    if os.path.exists(save_to):
        print('not downloading {0} since it exists locally'.format(save_to))
        return

    # try all possible sources one by one
    for url in sources[:-1]:
        # make five attempts per source
        for i in range(5):
            # first attempt to get a response
            response = urlopen(url)

            # handling redirections
            u = urlopen(response.geturl())

            meta = u.info()
            if meta.get('Content-Length') and len(meta.get('Content-Length')) > 0:
                filesz = int(meta.get('Content-Length'))
                if os.path.exists(save_to) and os.path.getsize(save_to) == filesz:
                    print('not downloading {0} since it exists locally'.format(save_to))
                    return

                print('downloading: {0} ({1} bytes)...'.format(save_to, filesz), end=' ')
                with open(save_to, 'wb') as fp:
                    block_sz = 8192
                    while True:
                        buff = u.read(block_sz)
                        if not buff:
                            break
                        fp.write(buff)

                print('done')
                break
        else:
            continue

        break  # successfully got the file
    else:
        assert 0, 'something went wrong -- cannot download {0}'.format(save_to)


#
#==============================================================================
def extract_archive(archive, solver, put_inside = False):
    """
        Unzips/untars a previously downloaded archive file.
    """

    print('extracting {0}'.format(archive))
    root = os.path.join('solvers', solver if put_inside else '')

    if archive.endswith('.tar.gz'):
        if os.path.exists(archive[:-7]):
            shutil.rmtree(archive[:-7])

        tfile = tarfile.open(archive, 'r:gz')
        tfile.extractall(root)

        # normally, directory should be the first name
        # but glucose4.1 has some garbage in the archive
        for name in tfile.getnames():
            if not name.startswith('./.'):
                directory = name
                break
    elif archive.endswith('.zip'):
        if os.path.exists(archive[:-4]):
            shutil.rmtree(archive[:-4])

        myzip = zipfile.ZipFile(archive, 'r')
        myzip.extractall(root)
        directory = myzip.namelist()[0]
        directory = directory.rstrip('/').split('/')[0]
        myzip.close()

    if not put_inside and directory != solver:
        if os.path.exists(os.path.join('solvers', solver)):
            shutil.rmtree(os.path.join('solvers', solver))

        shutil.move(os.path.join('solvers', directory), os.path.join('solvers', solver))


#
#==============================================================================
def adapt_files(solver):
    """
        Rename and remove files whenever necessary.
    """

    print("adapting {0}'s files".format(solver))
    root = os.path.join('solvers', solver)

    for arch in to_extract[solver]:
        arch = os.path.join(root, arch)
        extract_archive(arch, solver, put_inside=True)

    for fnames in to_move[solver]:
        old = os.path.join(root, fnames[0])
        new = os.path.join(root, fnames[1])
        os.rename(old, new)

    for f in to_remove[solver]:
        f = os.path.join(root, f)
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.remove(f)


#
#==============================================================================
def patch_solver(solver):
    """
        Applies a patch to a given solver.
    """

    print('patching {0}'.format(solver))

    if platform.system() != 'Windows':
        cmd = 'cd solvers/{0} && patch -p2 < ../patches/{0}.patch'.format(solver)
    else:
        cmd = 'wsl patch -p0 < solvers/patches/{0}.patch'.format(solver)

    os.system(cmd)


#
#==============================================================================
def compile_solver(solver):
    """
        Compiles a given solver as a library.
    """

    print('compiling {0}'.format(solver))
    os.system('cd solvers/{0} && make && cd ../..'.format(solver))
