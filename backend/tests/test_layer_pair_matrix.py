"""The eight layers as pairs, each with the guard that compares it — and the one cell that is empty.

The objective claims **八层对齐**: 模型, 迁移, schema, repository, service, API, hook, 页面. Round 229 found that **two
green checks can compare two different pairs and leave a third uncompared**, so "aligned" needs a matrix rather than an
adjective.

**Measured the honest way, by name rather than by keyword overlap.** A term-overlap proxy was tried first and reported
zero empty cells, **which was a false positive of the proxy**: it matched `test_error_envelope.py` as a guard for
`API ↔ hook` because that file mentions both `endpoints/` and `router`. Round 213's rule applies — *a proxy tells you where
to look, not what is true.*

So each pair below names **the file that actually compares the two things**, and the test asserts that file exists. **The
one pair nothing compares is named as such**, because that is the finding round 229 produced and it belongs in a record
rather than in a gap between two green checks.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

# pair -> (the test that compares it, what it compares). **A pair with no guard says WHY it has none**, so that adding one
# is a decision rather than an oversight.
GUARDED: dict[str, tuple[str, str]] = {
    "模型 <-> schema": (
        "test_schema_model_alignment.py",
        "every schema field that is not a column is derived, an input or a nested collection, in both directions",
    ),
    "迁移 <-> 活库": (
        "test_migration_reproduces_live_schema.py",
        "a database built from `alembic upgrade head` matches the live database, column by column",
    ),
    "模型 <-> 活库": (
        "test_model_schema_parity.py",
        "the models' declarations match the live schema, in both directions",
    ),
    "repository <-> 谓词": (
        "test_repository_predicate_coverage.py",
        "every repository scan of a soft-deletable model carries the `is_deleted` predicate",
    ),
    "service <-> 谓词": (
        "test_data_scope_coverage.py",
        "every service that should scope its reads does, with the call named",
    ),
    "API <-> hook": (
        "test_hook_route_alignment.py",
        "every hook URL exists in the API, so a hook cannot call a route nobody ever defined",
    ),
    "hook <-> 页面": (
        "test_page_data_use.py",
        "every page uses the hook layer rather than a direct fetch",
    ),
    "层与层之间的方向": (
        "test_layer_parity.py",
        "the layer edges point one way, including the three that were removed",
    ),
}

# **The cell round 229 found empty, and it is the pair that matters most for the objective's first layer.**
UNGUARDED: dict[str, str] = {
    "模型 <-> 迁移链": (
        "nothing compares the columns the models declare with the columns the migration chain creates: "
        "`test_schema_model_alignment.py` compares schemas with models, and `test_migration_reproduces_live_schema.py` "
        "compares the chain with the live database. **An `accounting_settlements` table that migration 0026 creates and no "
        "model declares passes both** (measured in round 229)."
    ),
}


def test_every_guarded_pair_names_a_test_file_that_exists():
    missing: list[str] = []
    for pair, (filename, _) in GUARDED.items():
        if not (BACKEND / "tests" / filename).is_file() and not (
            BACKEND / "integration_tests" / filename
        ).is_file():
            missing.append(f"{pair} -> {filename}")

    assert missing == [], (
        "these pairs name a guard file that does not exist, so the matrix is describing a repository this is not:\n  "
        + "\n  ".join(missing)
    )


def test_every_entry_says_what_it_compares():
    """Round 209's convention: a reviewed entry carries its reason, not only its name."""
    thin = [pair for pair, (_, reason) in GUARDED.items() if len(reason.strip()) < 40]
    assert thin == [], f"these matrix entries name a file without saying what it compares: {thin}"

    thin_unguarded = [pair for pair, reason in UNGUARDED.items() if len(reason.strip()) < 60]
    assert thin_unguarded == [], (
        "an unguarded pair has to say why nothing guards it, or the next reader cannot tell a decision from an oversight: "
        f"{thin_unguarded}"
    )


def test_the_unguarded_pair_is_the_one_round_229_measured():
    """If somebody builds that guard, this test is the reminder to move the cell rather than delete it."""
    assert "模型 <-> 迁移链" in UNGUARDED, (
        "the empty cell has been removed from this matrix. **If a guard now compares the models with the migration chain, "
        "move it into `GUARDED` with what it compares** — do not simply delete the record, because the pair was empty for "
        "the whole of this session's work."
    )
    assert "accounting_settlements" in UNGUARDED["模型 <-> 迁移链"], (
        "the empty cell no longer names the concrete example that proves it is empty"
    )
