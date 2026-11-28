from lxml import etree
def parse_items(xml_data):
    try:
        root = etree.fromstring(xml_data, etree.XMLParser(resolve_entities=True, no_network=False, huge_tree=True))
    except etree.XMLSyntaxError as e:
        raise ValueError(str(e))
    return [e.text or "" for e in root.iter("item")]
