============================
:fas:`file-alt;fa-fw` Papers
============================

pyecsca: Reverse engineering black-box elliptic curve cryptography via side-channel analysis
============================================================================================

Jan Jancar, Vojtech Suchanek, Petr Svenda, Vladimir Sedlacek, Lukasz Chmielewski

`CHES 2024, Halifax, Canada <https://ches.iacr.org/2024/>`_

.. grid::
    :margin: 2 0 0 2
    :padding: 2 0 0 2

    .. grid-item::
        :columns: auto

        .. button-link:: _static/pyecsca_ches24.pdf
            :color: secondary

            :fas:`file-alt;fa-fw` Preprint

    .. grid-item::
        :columns: auto

        .. button-link:: https://github.com/J08nY/pyecsca-artifact
            :color: secondary

            :fas:`file-zipper;fa-fw` Artifact

.. dropdown:: BibTeX
    :color: secondary
    :name: pyecsca-bibtex
    :class-container: bibtex-dropdown

    .. code-block:: Bibtex

        @InProceedings{2024-ches-jancar,
          title = {pyecsca: Reverse engineering black-box elliptic curve cryptography via side-channel analysis},
          author = {Jan Jancar and Vojtech Suchanek and Petr Svenda and Vladimir Sedlacek and Lukasz Chmielewski},
          booktitle = {IACR Transactions on Cryptographic Hardware and Embedded Systems},
          publisher = {Ruhr-University of Bochum},
          year = {2024},
          doi = {10.46586/tches.v2024.i4.355-381},
          url = {https://tches.iacr.org/index.php/TCHES/article/view/11796},
          pages = {355–381},
        }

Abstract
--------

Side-channel attacks on elliptic curve cryptography (ECC) often assume a
white-box attacker who has detailed knowledge of the implementation choices taken
by the target implementation. Due to the complex and layered nature of ECC, there
are many choices that a developer makes to obtain a functional and interoperable
implementation. These include the curve model, coordinate system, addition formulas,
and the scalar multiplier, or lower-level details such as the finite-field multiplication
algorithm. This creates a gap between the attack requirements and a real-world
attacker that often only has black-box access to the target – i.e., has no access to
the source code nor knowledge of specific implementation choices made. Yet, when
the gap is closed, even real-world implementations of ECC succumb to side-channel
attacks, as evidenced by attacks such as TPM-Fail, Minerva, the Side Journey to
Titan, or TPMScan.

We study this gap by first analyzing open-source ECC libraries for insight into real-
world implementation choices. We then examine the space of all ECC implementations
combinatorially. Finally, we present a set of novel methods for automated reverse
engineering of black-box ECC implementations and release a documented and usable
open-source toolkit for side-channel analysis of ECC called **pyecsca**.

Our methods turn attacks around: instead of attempting to recover the private key,
they attempt to recover the implementation configuration given control over the
private and public inputs. We evaluate them on two simulation levels and study the
effect of noise on their performance. Our methods are able to 1) reverse-engineer
the scalar multiplication algorithm completely and 2) infer significant information
about the coordinate system and addition formulas used in a target implementation



ECTester: Reverse-engineering side-channel countermeasures of ECC implementations
=================================================================================

Vojtech Suchanek, Jan Jancar, Jan Kvapil, Petr Svenda, Lukasz Chmielewski

`CHES 2025, Kuala Lumpur, Malaysia <https://ches.iacr.org/2025/>`_

.. grid::
    :margin: 2 0 0 2
    :padding: 2 0 0 2

    .. grid-item::
        :columns: auto

        .. button-link:: _static/ectester_ches25.pdf
            :color: secondary

            :fas:`file-alt;fa-fw` Preprint

    .. grid-item::
        :columns: auto

        .. button-link:: https://github.com/crocs-muni/ECTester
            :color: secondary

            :fas:`file-zipper;fa-fw` Artifact

.. dropdown:: BibTeX
    :color: secondary
    :name: pyecsca-bibtex
    :class-container: bibtex-dropdown

    .. code-block:: Bibtex

        @InProceedings{2025-ches-jancar,
          title = {ECTester: Reverse-engineering side-channel countermeasures of ECC implementations},
          author = {Vojtech Suchanek and Jan Jancar and Jan Kvapil and Petr Svenda and Lukasz Chmielewski},
          booktitle = {IACR Transactions on Cryptographic Hardware and Embedded Systems},
          publisher = {Ruhr-University of Bochum},
          year = {2025}
        }

Abstract
--------

Developers implementing elliptic curve cryptography (ECC) face a wide
range of implementation choices created by decades of research into elliptic curves.
The literature on elliptic curves offers a plethora of curve models, scalar multipliers,
and addition formulas, but this comes with the price of enabling attacks to also
use the rich structure of these techniques. Navigating through this area is not
an easy task and developers often obscure their choices, especially in black-box
hardware implementations. Since side-channel attackers rely on the knowledge of the
implementation details, reverse engineering becomes a crucial part of attacks.

This work presents **ECTester** – a tool for testing black-box ECC implementations.
Through various test suites, ECTester observes the behavior of the target implementation
against known attacks but also non-standard inputs and elliptic curve parameters.
We analyze popular ECC libraries and smartcards and show that some libraries and
most smartcards do not check the order of the input points and improperly handle
the infinity point. Based on these observations, we design new techniques for
reverse-engineering scalar randomization countermeasures that are able to distinguish
between group scalar randomization, additive, multiplicative or Euclidean splitting.
Our techniques do not require side-channel measurements; they only require the
ability to set custom domain parameters, and are able to extract not only the size but
also the exact value of the random mask used. Using the techniques, we successfully
reverse-engineered the countermeasures on 13 cryptographic smartcards from 5 major
manufacturers – all but one we tested on. Finally, we discuss what mitigations can
be applied to prevent such reverse engineering, and whether it is possible at all.
