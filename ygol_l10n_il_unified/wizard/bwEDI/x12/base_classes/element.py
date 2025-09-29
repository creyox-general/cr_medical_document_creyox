# -*- coding: utf-8 -*-
import logging
import pprint as pp

from .errors import FieldValidationError

_logger = logging.getLogger(__name__)


def modify_string_if_hebrew(s):
    """
    Checks if a string contains any Hebrew characters. If it does,
    tries to move the text inward by adding spaces at the beginning and end
    without overwriting the text itself, maintaining the string's length.

    Parameters:
    s (str): The input string to check and possibly modify.

    Returns:
    str: The modified string, if it contains Hebrew characters, or the original string if not.
    """
    # Check if the string contains any Hebrew characters
    has_hebrew = any('\u0590' <= char <= '\u05FF' for char in s)

    s_list = list(s)

    if has_hebrew:

        if s_list[0] == ' ' and s_list[-1] != ' ':
            if s_list[1] == ' ':
                s_list.append(' ')
                s_list = s_list[1:]
            else:
                s_list[-1] = ' '

        elif s_list[0] != ' ' and s_list[-1] == ' ':
            if s_list[-2] == ' ':
                s_list.insert(0, ' ')
                s_list = s_list[:-1]
            else:
                s_list[0] = ' '

        elif s_list[0] != ' ' and s_list[-1] != ' ':
            s_list[0] = ' '
            s_list[-1] = ' '
        else:
            pass

    return ''.join(s_list)


def format_number_decimal(number, digits: int, decimal_digits: int, drop_sign=False):
    if number is None or number == 'False' or not number:
        number = 0
    else:
        number = float(number)

    # Determine the sign
    sign = "+" if number >= 0 else "-"

    # Remove the sign for processing the absolute value
    abs_number = abs(number)

    # Calculate the required format string
    format_string = f"{{0:{1}.{decimal_digits}f}}"

    # Format the number according to the given number of digits
    formatted_number = format_string.format(abs_number).replace('.', '')
    formatted_number = formatted_number.replace(' ', '')

    # Ensure the string is the correct length by padding with leading zeros
    padded_number = formatted_number.zfill(digits + decimal_digits)

    total_digits = digits + decimal_digits
    formatted_number = padded_number[:total_digits]

    # Combine the sign with the formatted number
    if drop_sign:
        return f"{formatted_number}"
    else:
        return f"{sign}{formatted_number}"


def format_number(number, digits: int):
    if number is None or number == 'False' or not number:
        number = 0
    # Convert the number to an absolute integer
    abs_number = abs(int(number))

    # Convert to string and pad with leading zeros if necessary
    formatted_number = str(abs_number).zfill(digits)

    # If the formatted number is longer than the specified digits, truncate it
    if len(formatted_number) > digits:
        formatted_number = formatted_number[:digits]

    return formatted_number


def format_string(input_string, digits: int):
    # Convert the input to a string (in case it's not already)
    input_string = str(input_string)
    if input_string == "False":
        input_string = ''

    formatted_string = input_string.ljust(digits)

    # If the formatted string is longer than the specified digits, truncate it
    if len(formatted_string) > digits:
        formatted_string = formatted_string[:digits]

    formatted_string = modify_string_if_hebrew(formatted_string)

    return formatted_string


class Element(object):
    """A generic segment"""

    def __init__(
            self,
            name: str = "",
            json_name: str = "",
            description: str = "",
            length: int = None,
            content: str = "",
            numeric: bool = False,
            decimal: int = 0,
    ):
        self.numeric = numeric
        self.decimal = decimal
        self.is_amount = bool(decimal)
        self.name = name
        self.json_name = json_name
        self.description = description
        self.__content = ''
        self.content = content

        if length is not None:
            self.length = length
        elif self.content == self.name:
            self.length = len(self.content)
        else:
            self.length = 1

    def validate(self, report):
        """Validate the element"""
        # self._is_field_too_short(report)
        # self._is_field_too_long(report)
        pass

    def _is_field_too_short(self, report):
        """
        Determine if the field content is too short.
        :param content_length: current content length.
        :param report: the validation report to append errors.
        """
        if len(str(self)) < self.length:
            report.add_error(
                FieldValidationError(
                    msg=f"Field {self.name} is too short. Found {len(str(self))} characters, expected "
                        f"{self.length} characters.",
                    segment=self,
                )
            )

    def _is_field_too_long(self, report):
        """
        Determine if the field content is too long.
        :param content_length: current content length.
        :param report: the validation report to append errors.
        """
        if len(str(self)) > self.length:
            report.add_error(
                FieldValidationError(
                    msg=f"Field {self.name} is too long. Found {len(str(self))} characters, "
                        f"expected {self.length} characters.",
                    segment=self,
                )
            )

    def to_dict(self):
        return {
            "name": self.name,
            "json_name": self.json_name,
            "length": self.length,
            "content": self.content,
            "numeric": self.numeric,
            'decimal': self.decimal
        }

    def __str__(self):
        if self.__content is None:
            content = ''
        else:
            content = self.__content

        if self.numeric and self.decimal:
            res = format_number_decimal(content, self.length - self.decimal, self.decimal, drop_sign=True)
        elif not self.numeric and self.decimal:
            res = format_number_decimal(content, (self.length - self.decimal) - 1, self.decimal)
        elif self.numeric and not self.decimal:
            res = format_number(content, self.length)
        else:
            res = format_string(content, self.length)

        if len(res) != self.length:
            p = self.to_dict()
            p['res'] = res
            _logger.warning(str(p))

        return res

    @property
    def content(self) -> str:
        return str(self.__content)

    @content.setter
    def content(self, value: str):
        if value is None:
            self.__content = ''
        else:
            self.__content = str(value)
