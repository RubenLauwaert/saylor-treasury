from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from data_repositories.public_entity_repo import PublicEntityRepository
from api.dependencies import get_entity_repository
from api.models.entities import EntityList, EntityDetail
import time

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=EntityList)
async def get_entities(
    repo: PublicEntityRepository = Depends(get_entity_repository),
):
    """Get a list of all entities with optional filtering."""
    start_time = time.time()

    # Use the new optimized repository method
    entity_list = repo.get_entities_summary_for_api()

    end_time = time.time()
    print(f"Entities API response time: {end_time - start_time:.4f} seconds")

    return entity_list


@router.get("/{ticker}", response_model=EntityDetail)
async def get_entity_by_ticker(
    ticker: str, repo: PublicEntityRepository = Depends(get_entity_repository)
):
    """Get detailed information about a specific entity by ticker symbol."""
    start_time = time.time()

    # Use the new optimized repository method
    entity_detail = repo.get_entity_detail_for_api(ticker)
    if not entity_detail:
        raise HTTPException(
            status_code=404, detail=f"Entity with ticker {ticker} not found"
        )

    end_time = time.time()
    print(f"Entity detail API response time: {end_time - start_time:.4f} seconds")

    return entity_detail
