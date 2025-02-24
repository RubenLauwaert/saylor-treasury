from typing import List, Optional
import xml.etree.ElementTree as ET
import pandas as pd
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
    def __init__(self, xbrl_string, ticker: str):
        """
        Initialize the parser with an XBRL string.
        """
        self.tree = ET.ElementTree(ET.fromstring(xbrl_string))
        self.root = self.tree.getroot()
        self.ticker = ticker
        self.namespaces: dict[str,str]= extract_namespaces(xbrl_string)
        self.entity_namespace = self.namespaces.get(self.ticker.lower())
        self.bitcoin_tag_keywords: List[str] = ["Bitcoin", "Crypto", "BTC", "DigitalAsset"]
        self.bitcoin_tags: List[str] = self.get_bitcoin_related_tags()
        
    # Get entity defined tags
    
    def get_entity_defined_tags(self) -> set[str]:
        """
        Get entity defined tags from the XBRL file.
        """
        
        entity_defined_tags = set([element.tag.split('}')[1] for element in self.tree.iter() if self.entity_namespace in element.tag.lower()])
        
        return entity_defined_tags
    
    def get_bitcoin_related_tags(self) -> set[str]:
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
    
   

