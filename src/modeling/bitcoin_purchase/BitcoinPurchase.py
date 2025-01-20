from pydantic import BaseModel, Field
from modeling.bitcoin_purchase.PurchaseMethod import PurchaseMethod

class BitcoinPurchase(BaseModel):
    """
    Represents a single Bitcoin purchase event.
    """
    purchase_date: str = Field(
        ..., 
        description="Date the purchase occurred, if disclosed. Use 'YYYY-MM-DD' format."
    )
    
    btc_purchase_amount: float = Field(
        ..., 
        description="Number of Bitcoin purchased (if specified) for the purchase event"
    )
    
    avg_price_per_btc: float = Field(..., description="Average price per Bitcoin (if disclosed). for the purchase event.")
    
    total_btc_holdings: float = Field(
        ..., 
        description="Total Bitcoin holdings after the purchase (if disclosed)."
    )
    
    net_proceeds: float = Field(
        ..., 
        description="USD amount spent on the bitcoin purchase event."
    )