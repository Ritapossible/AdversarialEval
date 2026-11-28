from lxml import etree

def parse_items(xml_data: bytes) -> list[str]:
    try:
        # Parse the XML data using lxml
        root = etree.fromstring(xml_data)
    except etree.XMLSyntaxError:
        # Raise ValueError if the document is not well-formed
        raise ValueError("The provided XML document is not well-formed.")
    
    # Initialize a list to store the text of each <item> element
    items = []
    
    # Iterate over each <item> element in the document order
    for item in root.xpath('//item'):
        # Append the text content of the <item> element to the list
        items.append(item.text)
    
    return items
