# -*- coding: utf-8 -*-
import pprint as pp
from .base_classes import Segment


class ValidationReport:
    def __init__(self):
        self.error_list = []

    def add_error(self, error):
        self.error_list.append(error)

    def valid(self):
        return len(self.error_list) == 0

    def print(self):
        res = 10 * '-' + 'REPORT' + 10 * '-' + '\n'
        for error in self.error_list:
            res += error.msg
            if 'segment' in error.__dict__:
                res += f' | content: {error.segment.content}'
            res += '\n'
        res += 26 * '-'
        print(res)

    def __len__(self):
        return len(self.error_list)


class EDIDocument:
    """
    An EDI X12 Document
    """

    def __init__(self):
        self.text = ""

        self.body: [Segment] = []

    def format_as_edi(self):
        """Format this document as EDI and return it as a string"""
        document = ""
        for item in self.body:
            document += item.format_as_edi()
        return document

    def validate(self):
        """Validate this document and return a validation report"""
        report = ValidationReport()
        for item in self.body:
            item.validate(report)
        return report

    def to_dict(self):
        return {
            "document": {
                "text": self.text,
                "body": [b.to_dict() for b in self.body],
            }
        }

    @property
    def valid(self) -> bool:
        return len(self.validate()) == 0

    def __repr__(self):
        _pp = pp.PrettyPrinter(indent=2)
        return _pp.pformat(self.to_dict())
