1. ```requirements.txt```
```
lxml==4.9.3
```

2. ```python
from lxml import etree

def parse_items(xml_data: bytes) -> list[str]:
    try:
        tree = etree.fromstring(xml_data)
    except etree.XMLSyntaxError as e:
        raise ValueError("The document is not well-formed") from e
    
    items = []
    for item in tree.xpath('.//item'):
        if item.text is not None:
            items.append(item.text.strip())
    
    return items
```