from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from data_repositories.public_entity_repo import PublicEntityRepository
from api.dependencies import get_entity_repository, get_api_key
from models.PublicEntity import PublicEntity

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=List[Dict])
async def get_entities(
    api_key: str = Depends(get_api_key),
    entity_type: Optional[str] = Query(
        None, description="Filter by entity type (e.g. 'operating')"
    ),
    sic: Optional[str] = Query(None, description="Filter by SIC code"),
    active_btc: Optional[bool] = Query(
        None, description="Filter for active bitcoin treasury entities only"
    ),
    repo: PublicEntityRepository = Depends(get_entity_repository),
):
    """Get a list of all entities with optional filtering."""

    if active_btc:
        entities = repo.get_active_bitcoin_treasury_entities()
    elif entity_type:
        entities = repo.get_entities_by_type(entity_type)
    elif sic:
        entities = repo.get_entities_by_sic(sic)
    else:
        entities = repo.get_entities_w_existing_ticker()

    # Return simplified entity data (exclude large nested objects)
    return [
        {
            "name": entity.name,
            "ticker": entity.ticker,
            "cik": entity.cik,
            "entity_type": entity.entity_type,
            "sic": entity.sic,
            "sicDescription": entity.sicDescription,
            "bitcoin_entity_tags": [tag for tag in entity.bitcoin_entity_tags],
            "total_btc_holdings": entity.total_btc_holdings,
            "has_official_holdings": len(entity.bitcoin_data.holding_statements_xbrl)
            > 0,
            "has_gen_ai_holdings": len(entity.bitcoin_data.holding_statements_gen_ai)
            > 0,
        }
        for entity in entities
    ]


@router.get("/{ticker}", response_model=Dict)
async def get_entity_by_ticker(
    ticker: str, repo: PublicEntityRepository = Depends(get_entity_repository)
):
    """Get detailed information about a specific entity by ticker symbol."""

    entity = repo.get_entity_by_ticker(ticker)
    if not entity:
        raise HTTPException(
            status_code=404, detail=f"Entity with ticker {ticker} not found"
        )

    # Basic bitcoin data summary
    bitcoin_data = {
        "total_btc_holdings": entity.total_btc_holdings,
        "holding_statement_count": len(entity.bitcoin_data.holding_statements_xbrl),
        "fair_value_statement_count": len(
            entity.bitcoin_data.fair_value_statements_xbrl
        ),
        "gen_ai_statement_count": len(
            entity.bitcoin_data.general_bitcoin_statements_gen_ai
        ),
        "treasury_update_count": len(entity.bitcoin_data.treasury_updates_gen_ai),
    }

    # Get official holdings from XBRL data
    official_holdings = []
    if entity.bitcoin_data.holding_statements_xbrl:
        for holding in entity.bitcoin_data.holding_statements_xbrl:
            official_holdings.append(
                {
                    "amount": holding.statement.amount,
                    "unit": holding.statement.unit,
                    "report_date": holding.statement.report_date,
                    "filing_url": holding.filing.url,
                    "file_date": holding.filing.file_date,
                    "source": "Official",
                }
            )

    # Get AI-generated holdings
    ai_holdings = []
    if entity.bitcoin_data.holding_statements_gen_ai:
        for holding_result in entity.bitcoin_data.holding_statements_gen_ai:
            for statement in holding_result.statements:
                ai_holdings.append(
                    {
                        "amount": statement.amount,
                        "unit": statement.unit,
                        "date": statement.date,
                        "confidence_score": statement.confidence_score,
                        "filing_url": holding_result.filing.url,
                        "file_date": holding_result.filing.file_date,
                        "source": "GenAI",
                    }
                )

    # Get AI-generated treasury updates
    treasury_updates = []
    if entity.bitcoin_data.treasury_updates_gen_ai:
        for update_result in entity.bitcoin_data.treasury_updates_gen_ai:
            for update in update_result.statements:
                treasury_updates.append(
                    {
                        "amount": update.amount,
                        "unit": update.unit,
                        "update_type": update.update_type,
                        "date": update.date,
                        "confidence_score": update.confidence_score,
                        "filing_url": update_result.filing.url,
                        "file_date": update_result.filing.file_date,
                        "source": "GenAI",
                    }
                )

    # Entity metadata
    return {
        "name": entity.name,
        "ticker": entity.ticker,
        "cik": entity.cik,
        "entity_type": entity.entity_type,
        "sic": entity.sic,
        "sicDescription": entity.sicDescription,
        "website": entity.website,
        "bitcoin_entity_tags": [tag for tag in entity.bitcoin_entity_tags],
        "bitcoin_data": bitcoin_data,
        "quarterly_holdings": sorted(
            official_holdings,
            key=lambda x: x["report_date"] if x.get("report_date") else "",
            reverse=True,
        ),
        "ai_holdings": sorted(
            ai_holdings, key=lambda x: x["date"] if x.get("date") else "", reverse=True
        ),
        "treasury_updates": sorted(
            treasury_updates,
            key=lambda x: x["date"] if x.get("date") else "",
            reverse=True,
        ),
        "filing_count": len(entity.bitcoin_filings),
    }
