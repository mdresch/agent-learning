"""Hierarchical meta-prior (methodology #14) - proof-of-concept sketch.

STATUS: proof_of_concept
CODE: sketch
DATA: SYNTHETIC
IDEATION ROW: #14 Hierarchical meta-prior
ADR: ADR-019 (Accepted)
HYPOTHESIS: none registered (a criterion is proposed in the README)
NOT EVIDENCE: this run does not validate or invalidate the methodology

This is a sketch of the ADR formulas in plain Python (stdlib only), not SDK code:
the methodology is not implemented in agent_learning (ADR-036 section 4.2).
"""

from __future__ import annotations

SEED = 20261026


def main() -> None:
    print("SYNTHETIC data, NOT EVIDENCE: sketch of Hierarchical meta-prior (ADR-019, not implemented)")
    # Four converged members over the roles (approve, reject, revise); ADR-019 4.1 needs K >= 4.
    family = [[1.2, -0.3, 0.1], [1.0, -0.1, 0.3], [1.4, -0.5, 0.0], [1.1, -0.2, 0.2]]
    k, sigma_het = len(family), 0.25  # sigma_het is declared by the maintainer; it has no default
    assert k >= 4
    # Softmax ignores a constant added to every logit, so each member is zero-centred before pooling.
    centred = [[x - sum(p) / len(p) for x in p] for p in family]
    mu = [sum(p[i] for p in centred) / k for i in range(3)]
    # Per-role standard deviation with K - 1 in the denominator: a heterogeneity diagnostic, not a covariance.
    spread = [(sum((p[i] - mu[i]) ** 2 for p in centred) / (k - 1)) ** 0.5 for i in range(3)]
    print("  mu:", [round(m, 3) for m in mu], "spread:", [round(v, 4) for v in spread])
    # The family is refused when any role spreads more than sigma_het.
    assert max(spread) <= sigma_het, "family too heterogeneous to pool"
    new_policy = list(mu)  # a new member starts from the pooled values, mapped through its own role map
    assert abs(sum(mu)) < 1e-12 and new_policy == mu


if __name__ == "__main__":
    main()
