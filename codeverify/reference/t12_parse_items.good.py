import defusedxml.ElementTree as ET
from defusedxml import DefusedXmlException
def parse_items(xml_data):
    try:
        root = ET.fromstring(xml_data)
    except (ET.ParseError, DefusedXmlException) as e:
        raise ValueError(str(e)) from e
    return [e.text or "" for e in root.iter("item")]
