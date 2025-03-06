# FILE: repositories.py

import logging
from pymongo.collection import Collection
from pymongo import InsertOne, UpdateOne, DeleteOne
from typing import List, Optional
from models.PublicEntity import PublicEntity
from logging import Logger
from database import public_entity_collection
from models.util import BitcoinEntityTag
from api.models.entities import (
    EntitySummary,
    EntityDetail,
    BitcoinHolding,
    TreasuryUpdate,
    EntityList,
)


class PublicEntityRepository:

    logger: Logger

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection = public_entity_collection

    def get_all_entities(self) -> List[PublicEntity]:
        entities = self.collection.find()
        self.logger.info(
            f"Retrieved {self.collection.count_documents({})} entities from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_entity_by_cik(self, cik: str) -> Optional[PublicEntity]:
        entity = self.collection.find_one({"cik": cik})
        if entity:
            self.logger.info(f"Found entity with CIK {cik}.")
            return PublicEntity(**entity)
        self.logger.warning(f"No entity found with CIK {cik}.")
        return None

    def get_entity_by_ticker(self, ticker: str) -> Optional[PublicEntity]:
        entity = self.collection.find_one({"ticker": ticker})
        if entity:
            self.logger.info(f"Found entity with ticker {ticker}.")
            return PublicEntity(**entity)
        self.logger.warning(f"No entity found with ticker {ticker}.")
        return None

    def add_entity(self, entity: PublicEntity) -> str:
        result = self.collection.update_one(
            {"cik": entity.cik}, {"$set": entity.model_dump()}, upsert=True
        )
        if result.upserted_id:
            self.logger.info(f"Added new entity with CIK {entity.cik}.")
            return str(result.upserted_id)
        self.logger.info(f"Updated existing entity with CIK {entity.cik}.")
        return str(result.matched_count)

    def add_entities(self, entities: List[PublicEntity]) -> List[str]:
        operations = [
            UpdateOne({"cik": entity.cik}, {"$set": entity.model_dump()}, upsert=True)
            for entity in entities
        ]
        result = self.collection.bulk_write(operations)
        self.logger.info(f"Added or updated {len(result.upserted_ids)} entities.")
        return [str(id) for id in result.upserted_ids]

    def update_entity(self, cik: str, entity: PublicEntity) -> bool:
        result = self.collection.update_one({"cik": cik}, {"$set": entity.model_dump()})
        if result.modified_count > 0:
            self.logger.info(f"Updated entity with CIK {cik}.")
            return True
        self.logger.warning(f"No entity found with CIK {cik} to update.")
        return False

    def update_entities(self, entities: List[PublicEntity]) -> int:
        operations = [
            UpdateOne({"cik": entity.cik}, {"$set": entity.model_dump()})
            for entity in entities
        ]
        result = self.collection.bulk_write(operations)
        self.logger.info(f"Updated {result.modified_count} entities.")
        return result.modified_count

    def delete_entity(self, cik: str) -> bool:
        result = self.collection.delete_one({"cik": cik})
        if result.deleted_count > 0:
            self.logger.info(f"Deleted entity with CIK {cik}.")
            return True
        self.logger.warning(f"No entity found with CIK {cik} to delete.")
        return False

    def delete_entities(self, ciks: List[str]) -> int:
        operations = [DeleteOne({"cik": cik}) for cik in ciks]
        result = self.collection.bulk_write(operations)
        self.logger.info(f"Deleted {result.deleted_count} entities.")
        return result.deleted_count

    def get_bitcoin_mining_entities(self) -> List[PublicEntity]:
        entities = self.collection.find(
            {
                "bitcoin_entity_tags": {"$in": [BitcoinEntityTag.MINER.value]},
                "ticker": {"$exists": True, "$ne": None},
            }
        )
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'bitcoin_entity_tags': {'$in': [BitcoinEntityTag.MINER.value]}, 'ticker': {'$exists': True, '$ne': None}})} Bitcoin mining entities "
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_active_bitcoin_treasury_entities(self) -> List[PublicEntity]:
        entities = self.collection.find(
            {
                "bitcoin_entity_tags": {
                    "$in": [BitcoinEntityTag.ACTIVE_BTC_STRATEGY.value]
                },
                "ticker": {"$exists": True, "$ne": None},
            }
        )
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'bitcoin_entity_tags': {'$in': [BitcoinEntityTag.ACTIVE_BTC_STRATEGY.value]}, 'ticker': {'$exists': True, '$ne': None}})} active Bitcoin treasury entities "
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_entities_w_official_holdings(self) -> List[PublicEntity]:
        entities_w_holdings = self.collection.find(
            {
                "bitcoin_data.holding_statements_xbrl": {"$exists": True, "$ne": []},
                "ticker": {"$exists": True, "$ne": None},
            }
        )
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'bitcoin_data.holding_statements_xbrl': {'$exists': True, '$ne': []}, 'ticker': {'$exists': True, '$ne': None}})} entities with official bitcoin holdings from the collection."
        )
        return [PublicEntity(**entity) for entity in entities_w_holdings]

    def get_entities_by_type(self, entity_type: str) -> List[PublicEntity]:
        entities = self.collection.find(
            {"entity_type": entity_type, "ticker": {"$exists": True, "$ne": None}}
        )
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'entity_type': 'operating'})} operating entities from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_entities_by_sic(self, sic_str: str) -> List[PublicEntity]:
        entities = self.collection.find(
            {"sic": sic_str, "ticker": {"$exists": True, "$ne": None}}
        )
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'sic': sic_str})} entities with SIC {sic_str} from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_entities_w_existing_ticker(self) -> List[PublicEntity]:
        entities = self.collection.find({"ticker": {"$exists": True, "$ne": None}})
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'ticker': {'$exists': True, '$ne': None}})} entities with a ticker from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_foreign_entities(self) -> List[PublicEntity]:
        entities = self.collection.find(
            {
                "filing_metadatas": {"$elemMatch": {"form": "6-K"}},
                "filing_metadatas.form": {"$ne": "8-K"},
            }
        )
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'filing_metadatas': {'$elemMatch': {'form': '6-K'}}, 'filing_metadatas.form': {'$ne': '8-K'}})} foreign entities with form 6-K and no form 8-K from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    async def update_bitcoin_filings_for(self, public_entity: PublicEntity) -> bool:

        try:
            updated_entity = await public_entity.update_bitcoin_filings()
            self.add_entity(updated_entity)
            self.logger.info(
                f"Synced new bitcoin filings for entity: {public_entity.name}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Error syncing bitcoin filings for entity: {public_entity.name}"
            )
            return False

    def reset_bitcoin_filings(self) -> bool:

        try:
            entities = self.get_entities_w_existing_ticker()
            for entity in entities:
                entity.reset_bitcoin_filings()
            self.add_entities(entities)
            self.logger.info(f"Reset bitcoin filings for all entities")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting bitcoin filings for all entities: {e}")
            return False

    def reset_bitcoin_filing_parsed_states(self) -> bool:

        try:
            entities = self.get_entities_w_existing_ticker()
            for entity in entities:
                entity.reset_bitcoin_filings_all_states()
            self.add_entities(entities)
            self.logger.info(f"Reset bitcoin filing parsed states for all entities")
            return True
        except Exception as e:
            self.logger.error(
                f"Error resetting bitcoin filing parsed states for all entities: {e}"
            )
            return False

    async def identify_bitcoin_tags_for(self, public_entity: PublicEntity) -> bool:

        try:
            updated_entity = await public_entity.identify_bitcoin_tags()
            self.add_entity(updated_entity)
            self.logger.info(
                f"Identified bitcoin tags for entity: {public_entity.name}"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Error identifying bitcoin tags for entity: {public_entity.name} : {e}"
            )
            return False

    async def update_tenq_xbrl_facts_for(self, public_entity: PublicEntity) -> bool:

        try:
            updated_entity = (
                await public_entity.extract_official_bitcoin_data_tenqs_xbrl()
            )
            self.add_entity(updated_entity)
            self.logger.info(f"Updated bitcoin data for entity: {public_entity.name}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error updating bitcoin data for entity: {public_entity.name} : {e}"
            )
            return False

    async def update_gen_ai_statements_for(self, public_entity: PublicEntity) -> bool:

        try:
            # Update general statements for entity (Gen AI)
            entity_w_general_statements = (
                await public_entity.extract_general_statements_genai_eightks()
            )
            # Update parsed holding statements for entity (Gen AI)
            entity_w_holding_statements = (
                await entity_w_general_statements.extract_bitcoin_holdings_gen_ai_eightks()
            )
            # Update treasury update statemetns for entity (Gen AI)
            final_entity = (
                await entity_w_holding_statements.extract_treasury_updates_gen_ai()
            )
            self.add_entity(final_entity)
            self.logger.info(f"Updated bitcoin data for entity: {public_entity.name}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error updating bitcoin data for entity: {public_entity.name} : {e}"
            )
            return False

    async def update_gen_ai_holding_statements(
        self, public_entity: PublicEntity
    ) -> bool:

        try:
            updated_entity = (
                await public_entity.extract_bitcoin_holdings_gen_ai_eightks()
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Error updating bitcoin data for entity: {public_entity.name} : {e}"
            )
            return False

    ##################
    #      API       #
    ##################

    ##################
    #      API       #
    ##################

    def get_entities_summary_for_api(
        self,
        entity_type: Optional[str] = None,
        sic: Optional[str] = None,
        active_btc: Optional[bool] = None,
    ) -> EntityList:
        """
        Get entities with projection optimized for summary view.
        Returns EntityList model directly.
        """
        # Define query based on filters
        query = {"ticker": {"$exists": True, "$ne": None}}

        if active_btc:
            query["bitcoin_entity_tags"] = {
                "$in": [BitcoinEntityTag.ACTIVE_BTC_STRATEGY.value]
            }
        if entity_type:
            query["entity_type"] = entity_type
        if sic:
            query["sic"] = sic

        # Use projection to limit fields returned
        projection = {
            "name": 1,
            "ticker": 1,
            "cik": 1,
            "bitcoin_entity_tags": 1,
            "total_btc_holdings": 1,
            "bitcoin_data.holding_statements_xbrl": {
                "$slice": 1
            },  # Just need to check if array exists and has items
        }

        # Execute query with projection
        entity_dicts = self.collection.find(query, projection)

        # Transform to API models directly
        entity_summaries = []
        for entity in entity_dicts:
            entity_summaries.append(
                EntitySummary(
                    name=entity.get("name"),
                    ticker=entity.get("ticker"),
                    cik=entity.get("cik"),
                    bitcoin_entity_tags=entity.get("bitcoin_entity_tags", []),
                    bitcoin_holdings=entity.get("total_btc_holdings", 0.0),
                    has_official_holdings=len(
                        entity.get("bitcoin_data", {}).get(
                            "holding_statements_xbrl", []
                        )
                    )
                    > 0,
                )
            )

        self.logger.database(
            f"Retrieved {len(entity_summaries)} entities for API summary view"
        )
        return EntityList(count=len(entity_summaries), entities=entity_summaries)

    def get_entity_detail_for_api(self, ticker: str) -> Optional[EntityDetail]:
        """
        Get entity detail by ticker, returning the API model directly.
        """
        projection = {
            "name": 1,
            "ticker": 1,
            "cik": 1,
            "entity_type": 1,
            "sic": 1,
            "sicDescription": 1,
            "website": 1,
            "bitcoin_entity_tags": 1,
            "total_btc_holdings": 1,
            "bitcoin_data.holding_statements_xbrl": 1,
            "bitcoin_data.fair_value_statements_xbrl": 1,
            "bitcoin_data.holding_statements_gen_ai": 1,
            "bitcoin_data.treasury_updates_gen_ai": 1,
        }

        entity = self.collection.find_one({"ticker": ticker}, projection)

        if not entity:
            self.logger.warning(f"No entity found with ticker {ticker}")
            return None

        # Get filing count via aggregation
        filing_count = (
            self.collection.aggregate(
                [
                    {"$match": {"ticker": ticker}},
                    {"$project": {"count": {"$size": "$bitcoin_filings"}}},
                ]
            )
            .next()
            .get("count", 0)
        )

        # Process holdings data
        holdings = []
        bitcoin_data = entity.get("bitcoin_data", {})

        # Process official holdings
        for holding_data in bitcoin_data.get("holding_statements_xbrl", []):
            holdings.append(
                BitcoinHolding(
                    amount=holding_data.get("statement", {}).get("amount"),
                    unit=holding_data.get("statement", {}).get("unit"),
                    date_of_disclosure=holding_data.get("statement", {}).get(
                        "report_date"
                    ),
                    filing_url=holding_data.get("filing", {}).get("url"),
                    file_date=holding_data.get("filing", {}).get("file_date"),
                    source="Official",
                )
            )

        # Process AI-generated holdings
        for holding_result in bitcoin_data.get("holding_statements_gen_ai", []):
            for statement in holding_result.get("statements", []):
                holdings.append(
                    BitcoinHolding(
                        amount=statement.get("amount"),
                        unit=statement.get("unit"),
                        date_of_disclosure=statement.get("date"),
                        filing_url=holding_result.get("filing", {}).get("url"),
                        file_date=holding_result.get("filing", {}).get("file_date"),
                        source="AI",
                        confidence_score=statement.get("confidence_score"),
                    )
                )

        # Process treasury updates
        treasury_updates = []
        for update_result in bitcoin_data.get("treasury_updates_gen_ai", []):
            for update in update_result.get("statements", []):
                treasury_updates.append(
                    TreasuryUpdate(
                        amount=update.get("amount"),
                        update_type=update.get("update_type"),
                        unit=update.get("unit"),
                        date=update.get("date"),
                        filing_url=update_result.get("filing", {}).get("url"),
                        file_date=update_result.get("filing", {}).get("file_date"),
                        confidence_score=update.get("confidence_score"),
                    )
                )

        # Return the fully constructed EntityDetail model
        self.logger.database(f"Found entity with ticker {ticker} for API detail view")
        return EntityDetail(
            name=entity.get("name"),
            ticker=entity.get("ticker"),
            cik=entity.get("cik"),
            entity_type=entity.get("entity_type"),
            sic=entity.get("sic"),
            sic_description=entity.get("sicDescription"),
            website=entity.get("website"),
            bitcoin_entity_tags=entity.get("bitcoin_entity_tags", []),
            summary={
                "total_btc_holdings": entity.get("total_btc_holdings", 0.0),
                "official_holding_count": len(
                    bitcoin_data.get("holding_statements_xbrl", [])
                ),
                "ai_holding_count": sum(
                    len(r.get("statements", []))
                    for r in bitcoin_data.get("holding_statements_gen_ai", [])
                ),
                "treasury_update_count": sum(
                    len(r.get("statements", []))
                    for r in bitcoin_data.get("treasury_updates_gen_ai", [])
                ),
            },
            holdings=sorted(
                holdings,
                key=lambda x: x.date_of_disclosure if x.date_of_disclosure else "",
                reverse=True,
            ),
            treasury_updates=sorted(
                treasury_updates, key=lambda x: x.date if x.date else "", reverse=True
            ),
            filing_count=filing_count,
        )
