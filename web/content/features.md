---
title: Features
---

PySAT integrates a number of widely used state-of-the-art SAT solvers. All the
provided solvers are the original low-level implementations installed along
with PySAT. Note that the solvers\' source code *is not* a part of the
project\'s source tree and is downloaded and patched at every PySAT
installation. Note that originally the solvers\' source code was not
distributed with PySAT, which resulted in sequence of download and patch
operations for each solver during each installation of PySAT. This, however,
causes serious issues in case of using a proxy. As a result and since version
0.1.6.dev1, PySAT includes the solvers\' archive files in the distribution.

Currently, the following SAT solvers are supported (at this point, for
Minisat-based solvers only *core* versions are integrated):

-   CaDiCaL ([rel-1.0.3](https://github.com/arminbiere/cadical))
-   CaDiCaL ([rel-1.5.3](https://github.com/arminbiere/cadical))
-   CaDiCaL ([rel-1.9.5](https://github.com/arminbiere/cadical))
-   CaDiCaL ([rel-3.0.0](https://github.com/arminbiere/cadical))
-   Glucose ([3.0](http://www.labri.fr/perso/lsimon/glucose/))
-   Glucose ([4.1](http://www.labri.fr/perso/lsimon/glucose/))
-   Glucose ([4.2.1](http://www.labri.fr/perso/lsimon/glucose/))
-   Lingeling ([bbc-9230380-160707](http://fmv.jku.at/lingeling/))
-   MapleLCMDistChronoBT ([SAT competition 2018 version](http://sat2018.forsyte.tuwien.ac.at/solvers/main_and_glucose_hack/))
-   MapleCM ([SAT competition 2018 version](http://sat2018.forsyte.tuwien.ac.at/solvers/main_and_glucose_hack/))
-   Maplesat ([MapleCOMSPS_LRB](https://sites.google.com/a/gsd.uwaterloo.ca/maplesat/))
-   Mergesat ([3.0](https://github.com/conp-solutions/mergesat))
-   Minicard ([1.2](https://github.com/liffiton/minicard))
-   Minisat ([2.2 release](http://minisat.se/MiniSat.html))
-   Minisat ([GitHub version](https://github.com/niklasso/minisat))

In order to make SAT-based prototyping easier, PySAT integrates a variety of
cardinality encodings. All of them are implemented from scratch in C++. The
list of cardinality encodings included is the following:

-   pairwise[^8]
-   bitwise[^8]
-   sequential counters[^9]
-   sorting networks[^4]
-   cardinality networks[^2]
-   ladder/regular[^1] [^5]
-   totalizer[^3]
-   modulo totalizer[^7]
-   iterative totalizer[^6]

Furthermore, PySAT supports a number of encodings of pseudo-Boolean
constraints listed below. This is done by exploiting a third-party library
[Pindakaas](https://pypi.org/project/pindakaas/)[^10].

-   binary decision diagrams (BDD)[^11] [^12]
-   sequential weight counters[^13]
-   sorting networks[^11]
-   adder networks[^11]
-   binary merge[^14]
-   the watchdog encoding[^15]
-   the generalized totalizer[^16]
-   and the mixed radix encoding[^17]

[^1]: Carlos Ansótegui, Felip Manyà. *Mapping Problems with Finite-Domain
    Variables to Problems with Boolean Variables*. SAT (Selected Papers) 2004.
    pp. 1-15

[^2]: Roberto Asin, Robert Nieuwenhuis, Albert Oliveras, Enric
    Rodriguez-Carbonell. *Cardinality Networks and Their Applications*. SAT
    2009. pp. 167-180

[^3]: Olivier Bailleux, Yacine Boufkhad. *Efficient CNF Encoding of Boolean
    Cardinality Constraints*. CP 2003. pp. 108-122

[^4]: Kenneth E. Batcher. *Sorting Networks and Their Applications*. AFIPS
    Spring Joint Computing Conference 1968. pp. 307-314

[^5]: Ian P. Gent, Peter Nightingale. *A New Encoding of Alldifferent Into
    SAT*. In International workshop on modelling and reformulating constraint
    satisfaction problems 2004. pp. 95-110

[^6]: Ruben Martins, Saurabh Joshi, Vasco M. Manquinho, Inês Lynce.
    *Incremental Cardinality Constraints for MaxSAT*. CP 2014. pp. 531-548

[^7]: Toru Ogawa, Yangyang Liu, Ryuzo Hasegawa, Miyuki Koshimura, Hiroshi
    Fujita. *Modulo Based CNF Encoding of Cardinality Constraints and Its
    Application to MaxSAT Solvers*. ICTAI 2013. pp. 9-17

[^8]: Steven David Prestwich. *CNF Encodings*. Handbook of Satisfiability.
    2009. pp. 75-97

[^9]: Carsten Sinz. *Towards an Optimal CNF Encoding of Boolean Cardinality
    Constraints*. CP 2005. pp. 827-831

[^10]: Hendrik Bierlee, Jip J. Dekker. *Pindakaas*. Software.
    https://doi.org/10.5281/zenodo.10851855

[^11]: Niklas Eén, Niklas Sörensson. *Translating Pseudo-Boolean Constraints
    into SAT*. JSAT. vol. 2(1-4). 2006. pp. 1-26

[^12]: Ignasi Abío, Robert Nieuwenhuis, Albert Oliveras, Enric
    Rodríguez-Carbonell. *BDDs for Pseudo-Boolean Constraints -Revisited*.
    SAT. 2011. pp. 61-75

[^13]: Steffen Hölldobler, Norbert Manthey, Peter Steinke. *A Compact Encoding
    of Pseudo-Boolean Constraints into SAT*. KI. 2012. pp. 107-118

[^14]: Norbert Manthey, Tobias Philipp, Peter Steinke. *A More Compact
    Translation of Pseudo-Boolean Constraints into CNF Such That Generalized
    Arc Consistency Is Maintained*. KI. 2014. pp. 123-134

[^15]: Olivier Bailleux, Yacine Boufkhad, Olivier Roussel. *New
    Encodings of Pseudo-Boolean Constraints into CNF*. SAT 2009. pp. 181-194

[^16]: Saurabh Joshi, Ruben Martins, Vasco Manquinho. *Generalized Totalizer
    Encoding for Pseudo-Boolean Constraints*. CP 2015. pp. 200-209

[^17]: Anpeng Zha, Miyuki Koshimura, Hiroshi Fujita. *N-level Modulo-based
    CNF Encodings of Pseudo-Boolean Constraints for MaxSAT*. Constraints
    24(2). 2019. pp. 133-161

Finally, PySAT now supports arbitrary Boolean formulas with on-the-fly
clausification [^18] and provides (pre-)processing functionality [^19] by
exposing an interface to CaDiCaL's (version 1.5.3) preprocessor as well as
external user-defined engines following the IPASIR-UP interface [^20].

[^18]: G. S. Tseitin. *On the complexity of derivations in the propositional
    calculus*.  Studies in Mathematics and Mathematical Logic, Part II. pp.
    115–125, 1968

[^19]: Armin Biere, Matti Järvisalo, Benjamin Kiesl. *Preprocessing in SAT
    Solving*. In *Handbook of Satisfiability - Second Edition*. pp. 391-435

[^20]: Katalin Fazekas, Aina Niemetz, Mathias Preiner, Markus Kirchweger,
    Stefan Szeider, Armin Biere. *IPASIR-UP: User Propagators for CDCL*. SAT.
    2023. pp. 8:1-8:13
