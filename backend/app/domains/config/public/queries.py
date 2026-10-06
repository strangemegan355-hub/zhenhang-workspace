"""Reads the config domain publishes for callers outside it.

`app/services/business_settings_service.py` used to reach into `config_repository` directly; the
repository stays private to the domain and these three functions are the contract.
"""

from app.domains.config.repositories.config_repository import (
    create_config,
    get_config_by_key,
    update_config,
)

__all__ = ["create_config", "get_config_by_key", "update_config"]
