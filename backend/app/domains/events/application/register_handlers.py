from app.domains.events.application.event_bus import event_bus
from app.domains.events.event_handlers.audit_event_handlers import handle_quote_created
from app.domains.events.event_handlers.quote_export_handlers import handle_quote_export_requested


def register_default_event_handlers() -> None:
    if getattr(register_default_event_handlers, "_registered", False):
        return
    event_bus.register("quote.created", handle_quote_created)
    event_bus.register("quote.export.requested", handle_quote_export_requested)
    register_default_event_handlers._registered = True
