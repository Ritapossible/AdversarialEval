1. ```requirements.txt```
```
lxml==4.9.3
```

2. ```python
from lxml import etree

def parse_items(xml_data: bytes) -> list[str]:
    try:
        # Parse the XML data using lxml, which is robust against well-formedness issues
        root = etree.fromstring(xml_data)
    except etree.XMLSyntaxError as e:
        raise ValueError("XML document is not well-formed") from e

    # Use a generator expression to extract text from each <item> element
    items = [item.text.strip() for item in root.xpath("//item")]

    return items
```