from .x12 import EDIDocument, Segment, Element
from .x12.base_classes import all_segments as s


record_map = {
    'A000': s.A000,
    'A100': s.A100,
    'Z900': s.Z900,
    'C100': s.C100,
    'D110': s.D110,
    'D120': s.D120,
    'B100': s.B100,
    'B110': s.B110,
    'M100': s.M100,
}


def convert_summary_document(source: dict):
    document = EDIDocument()

    body = document.body
    body.append(s.A000().from_json(source['A000']))

    for key, value in source['counters'].items():
        segment = Segment()
        key_element = Element(
            name=key,
            content=key
        )

        value_element = Element(
            name="Count",
            numeric=True,
            length=15
        )
        value_element.content = value

        segment.fields = [key_element, value_element]
        body.append(segment)

    return document.format_as_edi()


def convert_unified_format(source: dict) -> str:
    """Parse the text document into an object
    :param source:  The text or file to parse into an EDI document.
    """
    document = EDIDocument()

    body = document.body

    for key, group in source.items():
        seg = record_map[key]
        for record in group:
            body.append(seg().from_json(record))

    return document.format_as_edi()

