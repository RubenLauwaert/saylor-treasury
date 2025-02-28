from typing import List, Optional
import xml.etree.ElementTree as ET
from services.ai.extract_xbrl_tag import XBRL_Extractor
import pandas as pd
from models.util import *
import re

def extract_namespaces(xbrl_string):
    """
    Extracts all namespace declarations from an XBRL document.
    :param xbrl_string: Raw XBRL XML content as a string.
    :return: Dictionary mapping prefixes to namespace URIs.
    """
    # Use regex to find all xmlns declarations in the root tag
    namespace_pattern = re.findall(r'xmlns(:\w+)?="([^"]+)"', xbrl_string)
    
    # Convert results into a dictionary {prefix: URI}
    namespaces = {prefix[1:] if prefix else "default": uri for prefix, uri in namespace_pattern}
    
    return namespaces



class Parser10QXBRL:
    
    instance_ns = '{http://www.xbrl.org/2003/instance}'
    xbrldi_ns = '{http://xbrl.org/2006/xbrldi}'
    
    
    def __init__(self, xbrl_url: str, xbrl_string: str, ticker: str):
        """
        Initialize the parser with an XBRL string.
        """
        self.tree = ET.ElementTree(ET.fromstring(xbrl_string))
        self.root = self.tree.getroot()
        self.ticker = ticker
        self.xbrl_url = xbrl_url
        self.namespaces: dict[str,str]= extract_namespaces(xbrl_string)
        self.entity_namespace = self.namespaces.get(self.ticker.lower())
        self.bitcoin_tag_keywords: List[str] = ["Bitcoin", "Crypto", "BTC", "DigitalAsset", "IntangibleAsset"]
        self.bitcoin_tags: List[str] = self._get_bitcoin_related_tags()
        
    # Get entity defined tags
    
    def _get_entity_defined_tags(self) -> set[str]:
        """
        Get entity defined tags from the XBRL file.
        """
        
        entity_defined_tags = set([element.tag.split('}')[1] for element in self.tree.iter() if self.entity_namespace in element.tag.lower()])
        
        return entity_defined_tags
    
    def _get_bitcoin_related_tags(self) -> set[str]:
        """
        Get entity defined tags that are related to Bitcoin.
        """
        defined_tags = set([element.tag for element in self.tree.iter()])
        bitcoin_related_tags = set()
        for tag in defined_tags:
            for keyword in self.bitcoin_tag_keywords:
                if keyword in tag:
                    bitcoin_related_tags.add(tag)
        return bitcoin_related_tags
    
    
    def _get_elements_with_tag(self, tag: str) -> List[ET.Element]:
        """
        Get all elements with a specific tag.
        """
        return [element for element in self.tree.iter() if tag == element.tag]
    
    
    
    def _get_context_for(self, context_id: str) -> dict[str,str]:
        """
        Get all context elements from the XBRL file.
        """
        context_elements: List[ET.Element] = [element for element in self.tree.iter() if "context" in element.tag]
        context = {}
        for context in context_elements:
            if context.attrib.get("id") == context_id:
                
                entity_text = None
                date_text = None
                coin_context = None
                entity = context.find(f"{self.instance_ns}entity")
                # Entity and coin context
                if entity is not None:              
                    identifier = entity.find(f"{self.instance_ns}identifier")
                    entity_text = identifier.text if identifier is not None else None
                    segment = entity.find(f"{self.instance_ns}segment")
                    if segment is not None:
                        explicit_member = segment.find(f"{self.xbrldi_ns}explicitMember")
                        if explicit_member is not None:
                            coin_context = explicit_member.text
                # Date       
                period = context.find(f"{self.instance_ns}period")
                if period is not None:
                    instant = period.find(f"{self.instance_ns}instant")
                    if instant is not None:
                        date_text = instant.text
                    else:
                        start_date = period.find(f"{self.instance_ns}startDate")
                        end_date = period.find(f"{self.instance_ns}endDate")
                        if start_date is not None and end_date is not None:
                            date_text = f"{end_date.text}"
                    
                    
                return { "entity": entity_text, "date": date_text, "coin_context": coin_context }
        return context
    
    
    
    async def extract_bitcoin_holdings(self) -> tuple[str, List[BitcoinHoldingsStatement]]:
        """
        Extract Bitcoin holdings from the XBRL file.
        """
        bitcoin_holdings = []
        ai_result_bitcoin_holdings = await XBRL_Extractor().extract_total_bitcoin_holdings_tag(self.bitcoin_tags)

      
        print(ai_result_bitcoin_holdings)
        ai_predicted_tag = ai_result_bitcoin_holdings.tag
        ai_confidence = ai_result_bitcoin_holdings.confidence

        # Check whether tag is official
        if ai_predicted_tag in self.bitcoin_tags and ai_confidence > 0.8:
            elements = self._get_elements_with_tag(ai_predicted_tag)
            bitcoin_holdings = []
            for element in elements:
                context_id = element.attrib.get("contextRef")
                context = self._get_context_for(context_id)
                unit_id = element.attrib.get("unitRef")
                decimals = element.attrib.get("decimals")
                # Bitcoin holding statement fields
                date = context.get("date")
                unit = "USD" if "usd" in unit_id.lower() else "BTC"
                # Value can be tricky as it can be denominated in USD or BTC or decimals fucking up the BTC amount
                value = 0
                if decimals is not None:
                    if decimals == "0" or decimals == "INF" or unit == "USD":
                        value = float(element.text) if element.text is not None else 0
                    # Now we have a "BTC" unit and decimals, now we need to be carful
                    else:
                        # First check if the decimal is an int
                        try:
                            decimals = int(decimals)
                            # In this case, the btc holdings is mostly reported as a float, ex. 7.2 , so the decimals would give 1 , we can skip this case
                            if decimals >= 0:
                                value = float(element.text) if element.text is not None else 0
                            # In the case it is negative, we need to multiply the value by 10^decimals, ex. 38000, decimals=-3 --> value = 38 , 
                            # This is common for holders that have a low amount of bitcoin and want to report it as an integer
                            else:
                                value = float(element.text) * 10**decimals if element.text is not None else 0
                        except:
                            decimals = 0
                else:
                    value = float(element.text) if element.text is not None else 0
                  
                bitcoin_holding_statement = BitcoinHoldingsStatement(amount=value, report_date=date, unit=unit, tag=ai_predicted_tag.split('}')[1])
                
                # Filter out holdings for other cryptocurrencies (Coinbase for example)
                coin_context = context.get("coin_context")
                if coin_context is not None:
                    if "bitcoin" in  coin_context.lower() or "btc" in coin_context.lower():
                        bitcoin_holdings.append(bitcoin_holding_statement)
                else:
                    bitcoin_holdings.append(bitcoin_holding_statement)
        
        return (self.xbrl_url, bitcoin_holdings)
    
    async def extract_bitcoin_fair_value(self) -> List[BitcoinFairValueStatement]:
        """
        Extract Bitcoin fair value from the XBRL file.
        """
        bitcoin_fair_value = []
        ai_result_bitcoin_fair_value = await XBRL_Extractor().extract_total_bitcoin_fair_value_tag(self.bitcoin_tags)

        ai_predicted_tag = ai_result_bitcoin_fair_value.tag
        ai_confidence = ai_result_bitcoin_fair_value.confidence
        print(f"Fair value : {ai_result_bitcoin_fair_value}")
        # Check whether tag is official
        if ai_predicted_tag in self.bitcoin_tags and ai_confidence > 0.85:
            elements = self._get_elements_with_tag(ai_predicted_tag)
            bitcoin_fair_value = []
            for element in elements:
                context_id = element.attrib.get("contextRef")
                context = self._get_context_for(context_id)
                unit = element.attrib.get("unitRef")
                
                # Fair value statement fields
                value = float(element.text)
                date = context.get("date")
                unit = "USD"
                
                fair_value_statement = BitcoinFairValueStatement(amount=value, date=date, unit=unit, tag=ai_predicted_tag.split('}')[1])
                
                # Filter out holdings for other cryptocurrencies (Coinbase for example)
                coin_context = context.get("coin_context")
                if coin_context is not None:
                    if "bitcoin" in  coin_context.lower() or "btc" in coin_context.lower():
                        bitcoin_fair_value.append(fair_value_statement)
                else:
                    bitcoin_fair_value.append(fair_value_statement)
        
        return bitcoin_fair_value

