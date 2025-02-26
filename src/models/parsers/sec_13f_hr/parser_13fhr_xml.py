import xml.etree.ElementTree as ET
import pandas as pd
import json


def parse_sec_xml(xml_file):
    # Define the namespace used in the XML file
    namespace = {'ns1': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'}
    
    # Parse the XML file
    tree = ET.ElementTree(ET.fromstring(xml_file))
    root = tree.getroot()
    
    # Extract infoTable entries
    data = []
    for info in root.findall(".//ns1:infoTable", namespace):
        entry = {
            "nameOfIssuer": info.find("ns1:nameOfIssuer", namespace).text,
            "titleOfClass": info.find("ns1:titleOfClass", namespace).text,
            "cusip": info.find("ns1:cusip", namespace).text,
            "value": int(info.find("ns1:value", namespace).text),
            "shares": int(info.find("ns1:shrsOrPrnAmt/ns1:sshPrnamt", namespace).text),
            "shareType": info.find("ns1:shrsOrPrnAmt/ns1:sshPrnamtType", namespace).text,
            "investmentDiscretion": info.find("ns1:investmentDiscretion", namespace).text,
            "votingSole": int(info.find("ns1:votingAuthority/ns1:Sole", namespace).text),
            "votingShared": int(info.find("ns1:votingAuthority/ns1:Shared", namespace).text),
            "votingNone": int(info.find("ns1:votingAuthority/ns1:None", namespace).text)
        }
        
        # Handle optional <putCall> field
        put_call = info.find("ns1:putCall", namespace)
        entry["putCall"] = put_call.text if put_call is not None else "N/A"
        
        data.append(entry)
    
    return data