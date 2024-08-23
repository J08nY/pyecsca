====================================
:fas:`server;fa-fw` ECC in Libraries
====================================

This page collects information about ECC implementations in open-source software. It was extracted
by source code analysis (i.e. we looked at the code and tried really hard to name what we see), so it
may or may not match the reality (whether due to a mistake or due to different naming choices).

We restricted ourselves to ECDH/ECDSA (on prime field curves) and X25519/Ed25519. In case libraries contain multiple
implementations we tried to document them clearly, along with the rules on how they pick one
(e.g. curve-based/architecture-based). Naming of scalar multipliers is tricky. Naming of coordinate systems
and formulas is taken from the `EFD <https://www.hyperelliptic.org/EFD/index.html>`__.


.. toctree::
   :titlesonly:
   :glob:
   :maxdepth: 2

   libraries/*
