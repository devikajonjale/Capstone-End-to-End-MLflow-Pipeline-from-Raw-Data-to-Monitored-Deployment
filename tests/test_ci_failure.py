"""Deliberately failing test used to prove the CI quality gate blocks merges.

This file lives only on branch test/deliberately-failing-ci-gate and will
never be merged to main. The PR raised from that branch is expected to show
a red CI run; it exists as evidence that CI does in fact gate pull requests,
which the project brief requires alongside a passing PR.
"""


def test_ci_gate_rejects_this_branch():
    # Intentional assertion failure so GitHub Actions reports a red check
    # and blocks the merge. Do not fix.
    assert False, (
        "This failure is intentional. See tests/test_ci_failure.py docstring. "
        "The branch test/deliberately-failing-ci-gate exists to prove the CI "
        "gate blocks defective pull requests."
    )
