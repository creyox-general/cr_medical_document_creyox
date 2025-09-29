# -*- coding: utf-8 -*-
import pprint as pp

from .element import Element


class Segment(object):
    def __init__(self):
        self.field_count = 0
        self.fields: list[Element] = []
        self.id = Element()
        self.segment_terminator = "\n"

    def validate(self, report):
        """
        Validate the segment by validating all elements.
        :param report: the validation report to append errors.
        """
        for field in self.fields:
            field.validate(report)

    def format_as_edi(self):
        """Format the segment into an EDI string"""
        return str(self)

    def to_json(self) -> dict:
        res = {}
        for element in self.fields[1:]:
            if element.content and element.json_name:
                res[element.json_name] = element.content
        return res

    def from_json(self, data: dict):
        element_map = self._json_to_element_map()
        for json_name, value in data.items():
            if json_name in element_map.keys():
                element_map[json_name].content = value
        return self

    def _json_to_element_map(self) -> dict:
        res = {}
        for element in self.fields[1:]:
            if element.json_name:
                res[element.json_name] = element
        return res

    def _all_fields_empty(self):
        """determine if all fields are empty"""
        for field in self.fields:
            if field.content != "":
                return False
        return True

    def _get_fields_as_string(self, out: str):
        """processes all the fields in the segment and returns the string representation"""

        for index, field in enumerate(self.fields):
            try:
                out += str(field)
            except ValueError as e:
                raise ValueError(f"Error processing field {field.name} of segment {self.id.name} "
                                 f"| value: {field.content} | type: {type(field.content)}") from e

        out = self._add_segment_terminator(out)

        return out

    def _add_segment_terminator(self, out):
        """Adds the segment terminator to the segment string"""
        out += self.segment_terminator
        return out

    def to_dict(self):
        return {
            "field_count": self.field_count,
            "fields": [field.to_dict() for field in self.fields],
            "segment_terminator": self.segment_terminator,
        }

    def __str__(self):
        """Return the segment as a string"""
        return self._get_fields_as_string("")

    def __getitem__(self, index: int):
        try:
            return self.fields[index]
        except IndexError:
            return Element()
