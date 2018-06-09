========
Features
========

PySAT integrates a number of widely used state-of-the-art SAT solvers. All the
provided solvers are the original low-level implementations installed along
with PySAT. Note that the solvers' source code *is not* a part of the project's
source tree and is downloaded and patched at every PySAT installation.

Currently, the following SAT solvers are supported (at this point, for
Minisat-based solvers only *core* versions are integrated):

-  Glucose (`3.0 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Glucose (`4.1 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Lingeling (`bbc-9230380-160707 <http://fmv.jku.at/lingeling/>`__)
-  Minicard (`1.2 <https://github.com/liffiton/minicard>`__)
-  Minisat (`2.2 release <http://minisat.se/MiniSat.html>`__)
-  Minisat (`GitHub version <https://github.com/niklasso/minisat>`__)

In order to make SAT-based prototyping easier, PySAT integrates a variety of
cardinality encodings. All of them are implemented from scratch in C++. The
list of cardinality encodings included is the following:

-  pairwise [7]_
-  bitwise [7]_
-  sequential counters [8]_
-  sorting networks [3]_
-  cardinality networks [1]_
-  ladder [4]_
-  totalizer [2]_
-  modulo totalizer [6]_
-  iterative totalizer [5]_

.. [1] Roberto Asin, Robert Nieuwenhuis, Albert Oliveras,
   Enric Rodriguez-Carbonell. *Cardinality Networks and Their Applications*.
   SAT 2009. pp. 167-180

.. [2] Olivier Bailleux, Yacine Boufkhad. *Efficient CNF Encoding of Boolean
   Cardinality Constraints*. CP 2003. pp. 108-122

.. [3] Kenneth E. Batcher. *Sorting Networks and Their Applications*.
   AFIPS Spring Joint Computing Conference 1968. pp. 307-314

.. [4] Ian P. Gent, Peter Nightingale. *A New Encoding of Alldifferent Into
   SAT*. In International workshop on modelling and reformulating constraint
   satisfaction problems 2004. pp. 95-110

.. [5] Ruben Martins, Saurabh Joshi, Vasco M. Manquinho, Inês Lynce.
   *Incremental Cardinality Constraints for MaxSAT*. CP 2014. pp. 531-548

.. [6] Toru Ogawa, Yangyang Liu, Ryuzo Hasegawa, Miyuki Koshimura,
   Hiroshi Fujita. *Modulo Based CNF Encoding of Cardinality Constraints and
   Its Application to MaxSAT Solvers*. ICTAI 2013. pp. 9-17

.. [7] Steven David Prestwich. *CNF Encodings*. Handbook of Satisfiability.
   2009. pp. 75-97

.. [8] Carsten Sinz. *Towards an Optimal CNF Encoding of Boolean
   Cardinality Constraints*. CP 2005. pp. 827-831
