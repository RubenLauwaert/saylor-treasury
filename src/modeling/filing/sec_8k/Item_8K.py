from pydantic import BaseModel
from typing import List, Optional, Union
from modeling.filing.sec_8k.ItemCode_8K import ItemCode_8K

class Item_8K(BaseModel):
    code: Optional[ItemCode_8K] = None
    subtitles: List[str] = []
    summary: Union[str, List[str]] = ""
    raw_text: str = ""

    class Config:
        use_enum_values = True