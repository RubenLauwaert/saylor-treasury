from fastapi import Depends
from typing import Dict, Optional
from data_repositories.public_entity_repo import PublicEntityRepository

# Removed API key authentication code


def get_entity_repository():
    """Dependency that provides a PublicEntityRepository instance."""
    return PublicEntityRepository()


# Dummy authentication function that always succeeds
async def get_api_key():
    """
    Placeholder authentication function.
    Currently returns None as authentication is disabled.
    """
    return None
