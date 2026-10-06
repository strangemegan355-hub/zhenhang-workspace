# app/domains — where the migration actually stands

The numbers below were counted, not estimated: non-`__init__` Python files and their lines per domain, and the
`ImportFrom` targets of every module in `app/api/v1/endpoints`. Re-count them the same way when the migration
moves — this file is a snapshot, and the structure alone is misleading: nine domain packages exist, and only four
of them carry code.

## The four that carry code

| domain | files | lines | sublayers with real content |
|---|---|---|---|
| `quote` | 15 | 1695 | `application` (4), `repositories` (1), `policies` (1), `public/queries.py` |
| `events` | 10 | 437 | `application` (2), `repositories` (2) |
| `file` | 10 | 404 | `application`, `infrastructure`, `repositories`, `policies` |
| `config` | 12 | 179 | `application`, `repositories`, `policies` |

`quote` holds roughly two thirds of all the Python under `app/domains`, and it is the only domain with a
`public/` package — which is what the legacy layer is allowed to import from (see `REVERSE_EDGES`).

## The five that are import shims, deliberately

`audit`, `auth`, `customer`, `machine` and `workflow` contain nothing but `__init__.py` files, each of the form:

```python
from app.services import machine_service

__all__ = ["machine_service"]
```

They are **not** empty scaffolding waiting to be filled. They re-export the legacy service so that
`from app.domains.machine import machine_service` resolves, letting an importer move to the domain path before the
implementation does. That re-export is exactly why `LEGACY_EDGES` in `tests/test_layer_parity.py` lists entries
like `("app/domains/machine/__init__.py", "app.services")` — the parity test records the direction, and this file
records that the direction is currently a facade.

Two consequences worth knowing before reading anything else here:

* **A file under a shim domain is not evidence that the module has moved.** Only the four domains above have
  implementation behind them.
* **`domain/` and `infrastructure/` are the thin layers.** Only `file` has an `infrastructure` directory, and no
  domain has a `domain/` directory with content, so the two layers that would make this architecture pay off are
  the two that are least developed.

## Endpoints: which layer they actually call

Of the forty endpoint modules that own business logic:

* **4 import only `app.domains`** — `ai`, `configs`, `files`, `quotes`;
* **36 import only `app.services`** — the legacy layer still owns them;
* **0 import both**;
* 3 import neither, being infrastructure-shaped: `health`, `notifications`, `realtime`.

So the migration has moved **4 of 40 endpoints** as measured in round 116, and the number is worth keeping visible: a module being
reachable through `app.domains.<name>` today says nothing about whether anything moved.
