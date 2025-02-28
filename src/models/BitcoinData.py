from pydantic import BaseModel, Field
from datetime import date
from models.util import *

class BitcoinData(BaseModel):

    
    holding_statements_xbrl: List[HoldingStatementTenQ] = Field(default=[], description="The list of official bitcoin holdings statements, extracted from parsed XBRL 10Q filigns")
    fair_value_statements: List[BitcoinFairValueStatement] = Field(default=[], description="The list of official bitcoin fair value statements, extracted from parsed XBRL 10Q filigns")
    
    # Information extracted out of bitcoin filings with Generative AI
    bitcoin_events: List[BitcoinEvent] = Field(default=[], description="The list of bitcoin events.")
    holding_statements_gen_ai: List[BitcoinHoldingsStatement] = Field(default=[], description="The list of official bitcoin holdings statements, extracted from parsed (8K's) filings with Generative AI")
    treasury_updates_gen_ai: List[BitcoinTreasuryUpdate] = Field(default=[], description="The list of bitcoin treasury updates, extracted from parsed (8K's) filings with Generative AI")
    
    # Setters
    
    def append_holding_statement_xbrl(self, holding_statement: HoldingStatementTenQ):
        # check if statement with same amount and report date already exists
        existing_statements = [existing_statement for existing_statement in self.holding_statements_xbrl if existing_statement.statement.report_date == holding_statement.statement.report_date and existing_statement.statement.amount == holding_statement.statement.amount]
        does_exist = len(existing_statements) > 0
        
        if not does_exist:
            self.holding_statements_xbrl.append(holding_statement)
        else:
            existing_statement = existing_statements[0]
            # Here we need to keep the existing statement but update the filing with the one that is the oldest
            new_statement_has_older_source = date.fromisoformat(holding_statement.filing.file_date) < date.fromisoformat(existing_statement.filing.file_date)
            if new_statement_has_older_source:
                self.holding_statements_xbrl.remove(existing_statement)
                self.holding_statements_xbrl.append(holding_statement)
                
        return self.holding_statements_xbrl
    
    def append_holding_statements_xbrl(self, holding_statements: List[HoldingStatementTenQ]):
        # Before adding ten-q holding statement, check if the statement already exists
        for statement in holding_statements:
            self.append_holding_statement_xbrl(statement)
                
                
