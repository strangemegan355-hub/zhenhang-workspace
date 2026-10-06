"""The events application package.

`register_default_event_handlers` is deliberately **not** re-exported here. Importing it from this facade made
`from app.domains.events.application.event_bus import event_bus` run the handler imports as well, because importing a
package runs its `__init__`; since `file_application_service` and `quote_application_service` both import the bus, that
closed a cycle through the handlers. Registration was already explicit at every entry point — `main.py`,
`workers/event_worker.py` and the event-dispatch integration test all call it — so the import belongs to them, from
`app.domains.events.application.register_handlers`.
"""

from app.domains.events.application.event_bus import event_bus

__all__ = ["event_bus"]
