---
title: To-Do
---

PySAT toolkit is a work in progress. Although it can already be helpful in
many practical settings (and it **was** successfully applied by its authors
for a number of times), it would be great if some of the following additional
features were implemented:

-   more SAT solvers to support (e.g.
    [CryptoMiniSat](https://github.com/msoos/cryptominisat/),
    [RISS](http://tools.computational-logic.org/content/riss.php) among
    many others)
-   formula *(pre-)processing*
-   lower level access to some of the solvers\' internal parameters
    (e.g. *variable activities*, etc.)
-   high-level support for arbitrary Boolean formulas (e.g. by
    Tseitin-encoding[^1] them internally)

All of these will require a significant effort to be made. Therefore, we would
like to encourage the SAT community to contribute and make PySAT a tool for an
easy and comfortable day-to-day use. :)

[^1]: G. S. Tseitin. *On the complexity of derivations in the propositional
    calculus*. Studies in Mathematics and Mathematical Logic, Part II. pp.
    115--125, 1968
