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
            :color: primary

            :fas:`file-alt;fa-fw` Preprint

    .. grid-item::
        :columns: auto

        .. button-link:: https://github.com/J08nY/pyecsca-artifact
            :color: primary

            :fas:`file-zipper;fa-fw` Artifact

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
