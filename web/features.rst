========
Features
========

PySAT integrates a number of widely used state-of-the-art SAT solvers. All the
provided solvers are the original low-level implementations installed along
with PySAT. Note that the solvers' source code *is not* a part of the project's
source tree and is downloaded and patched at every PySAT installation.

Currently, the following SAT solvers are supported (at this point, for
Minisat-based solvers only *core* versions are integrated):

-  CaDiCaL (`rel-1.0.3 <https://github.com/arminbiere/cadical>`__)
-  Glucose (`3.0 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Glucose (`4.1 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Lingeling (`bbc-9230380-160707 <http://fmv.jku.at/lingeling/>`__)
-  MapleLCMDistChronoBT (`SAT competition 2018 version <http://sat2018.forsyte.tuwien.ac.at/solvers/main_and_glucose_hack/>`__)
-  MapleCM (`SAT competition 2018 version <http://sat2018.forsyte.tuwien.ac.at/solvers/main_and_glucose_hack/>`__)
-  Maplesat (`MapleCOMSPS_LRB <https://sites.google.com/a/gsd.uwaterloo.ca/maplesat/>`__)
-  Minicard (`1.2 <https://github.com/liffiton/minicard>`__)
-  Minisat (`2.2 release <http://minisat.se/MiniSat.html>`__)
-  Minisat (`GitHub version <https://github.com/niklasso/minisat>`__)

In order to make SAT-based prototyping easier, PySAT integrates a variety of
cardinality encodings. All of them are implemented from scratch in C++. The
list of cardinality encodings included is the following:

-  pairwise [8]_
-  bitwise [8]_
-  sequential counters [9]_
-  sorting networks [4]_
-  cardinality networks [2]_
-  ladder/regular [1]_ [5]_
-  totalizer [3]_
-  modulo totalizer [7]_
-  iterative totalizer [6]_

.. [1] Carlos Ansótegui, Felip Manyà. *Mapping Problems with Finite-Domain
   Variables to Problems with Boolean Variables*. SAT (Selected Papers) 2004.
   pp. 1-15

.. [2] Roberto Asin, Robert Nieuwenhuis, Albert Oliveras,
   Enric Rodriguez-Carbonell. *Cardinality Networks and Their Applications*.
   SAT 2009. pp. 167-180

.. [3] Olivier Bailleux, Yacine Boufkhad. *Efficient CNF Encoding of Boolean
   Cardinality Constraints*. CP 2003. pp. 108-122

.. [4] Kenneth E. Batcher. *Sorting Networks and Their Applications*.
   AFIPS Spring Joint Computing Conference 1968. pp. 307-314

.. [5] Ian P. Gent, Peter Nightingale. *A New Encoding of Alldifferent Into
   SAT*. In International workshop on modelling and reformulating constraint
   satisfaction problems 2004. pp. 95-110

.. [6] Ruben Martins, Saurabh Joshi, Vasco M. Manquinho, Inês Lynce.
   *Incremental Cardinality Constraints for MaxSAT*. CP 2014. pp. 531-548

.. [7] Toru Ogawa, Yangyang Liu, Ryuzo Hasegawa, Miyuki Koshimura,
   Hiroshi Fujita. *Modulo Based CNF Encoding of Cardinality Constraints and
   Its Application to MaxSAT Solvers*. ICTAI 2013. pp. 9-17

.. [8] Steven David Prestwich. *CNF Encodings*. Handbook of Satisfiability.
   2009. pp. 75-97

.. [9] Carsten Sinz. *Towards an Optimal CNF Encoding of Boolean
   Cardinality Constraints*. CP 2005. pp. 827-831

Furthermore, PySAT supports a number of encodings of pseudo-Boolean
constraints listed below. This is done by exploiting a third-party library
`PyPBLib <https://pypi.org/project/pypblib/>`__  developed by the `Logic
Optimization Group <http://ulog.udl.cat/>`__ of the University of Lleida.
(PyPBLib is a wrapper over the known PBLib library [10]_.)

-  binary decision diagrams (BDD) [11]_ [12]_
-  sequential weight counters [13]_
-  sorting networks [11]_
-  adder networks [11]_
-  and binary merge [14]_

.. [10] Tobias Philipp, Peter Steinke. *PBLib - A Library for Encoding
    Pseudo-Boolean Constraints into CNF*. SAT 2015. pp. 9-16

.. [11] Niklas Eén, Niklas Sörensson. *Translating Pseudo-Boolean
    Constraints into SAT*. JSAT. vol. 2(1-4). 2006. pp. 1-26

.. [12] Ignasi Abío, Robert Nieuwenhuis, Albert Oliveras,
    Enric Rodríguez-Carbonell. *BDDs for Pseudo-Boolean Constraints -
    Revisited*. SAT. 2011. pp. 61-75

.. [13] Steffen Hölldobler, Norbert Manthey, Peter Steinke. *A Compact
    Encoding of Pseudo-Boolean Constraints into SAT*. KI. 2012.
    pp. 107-118

.. [14] Norbert Manthey, Tobias Philipp, Peter Steinke. *A More Compact
    Translation of Pseudo-Boolean Constraints into CNF Such That
    Generalized Arc Consistency Is Maintained*. KI. 2014. pp. 123-134
