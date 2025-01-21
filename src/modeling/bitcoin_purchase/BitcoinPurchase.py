from pydantic import BaseModel, Field
from modeling.bitcoin_purchase.PurchaseMethod import PurchaseMethod
from datetime import date

class CustomDate(BaseModel):
    Year: int
    Month: int
    Day: int
    
 
    
    def to_date(self) -> date:
        """
        Converts the CustomDate instance to a date object.
        """
        return date(self.Year, self.Month, self.Day)
    
    class Config:
        extra = "forbid"  # Disallow additional properties

class BitcoinPurchase(BaseModel):
    """
    Represents a single Bitcoin purchase event.
    """
    purchase_date: CustomDate = Field(
        ..., 
        description="Date the purchase occurred"
    )
    
    btc_purchase_amount: float = Field(
        ..., 
        description="Number of Bitcoin purchased (if specified) for the purchase event"
    )
    
    avg_purchase_price_per_btc: float = Field(..., description="Average price per Bitcoin (if disclosed). for the single purchase event.")
    
    total_btc_holdings: float = Field(
        ..., 
        description="Total Bitcoin holdings after the purchase (if disclosed)."
    )
    
    net_proceeds: float = Field(
        ..., 
        description="USD amount spent on the bitcoin purchase event."
    )
    
    class Config:
        extra = "forbid"  # Disallow additional properties