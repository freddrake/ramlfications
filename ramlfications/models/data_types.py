# -*- coding: utf-8 -*-
# Copyright (c) 2016 Spotify AB

from __future__ import absolute_import, division, print_function

import copy
import re

import attr
from six import iteritems

from ramlfications.utils.common import OrderedDict
from ramlfications.validate import *  # NOQA

from .base import BaseContent


RAML_MAX_INT = 2147483647


####
# TO CLEAN ->
RAML_DATA_TYPES = {}


def type_class(type_name):
    def func(klass):
        if type_name not in RAML_DATA_TYPES:
            RAML_DATA_TYPES[type_name] = klass
        return klass
    return func


@attr.s
class Property(object):
    """
    helper class for holding additional checks for object properties

    :param bool required: is this property mandatory
    :param <any> default: default value for this property
    :param <BaseDataType> data_type: type definition of the property
    """
    required = attr.ib(repr=False, default=False)
    default  = attr.ib(repr=False, default=None)
    type     = attr.ib(default='string')


def create_property(property_def):
    # we remove the attributes for the property in order to keep
    # only attributes needed for the type definition
    type_def = copy.copy(property_def)
    return Property(default=type_def.pop('default', None),
                    required=type_def.pop('required', False),
                    type=type_def.pop('type', 'string'))


def parse_properties(properties):
    # @todo: should parse k for syntax sugar
    if not properties:
        return None
    return OrderedDict([
        (k, create_property(v))
        for k, v in iteritems(properties)])


# <- TO CLEAN
####


@attr.s
class RAMLDataType(object):
    """
    Base class for all RAML-defined data types.

    :param string name: name of the type
    :param Content description: description for the type.
        This is a markdown Content with on the fly conversion to html using
        description.html
    :type string base type for this type
    """
    name         = attr.ib()
    display_name = attr.ib(repr=False, default=None)
    annotation   = attr.ib(repr=False, default=None)
    default      = attr.ib(repr=False, default=None)
    description  = attr.ib(repr=False, default="", convert=BaseContent)
    example      = attr.ib(repr=False, default=None)
    examples     = attr.ib(repr=False, default=None)
    # TODO: how to validate? See:
    # https://github.com/raml-org/raml-spec/blob/master/versions/raml-10/raml-10.md/#user-defined-facets  # NOQA
    facets       = attr.ib(repr=False, default=None)
    # TODO: Validation: if type is defined, schema can not be, and vice versa
    type         = attr.ib(repr=False, default=None)
    # TODO: how to implement deprecation warning
    schema       = attr.ib(repr=False, default=None, validator=defined_schema)
    usage        = attr.ib(repr=False, default=None)
    xml          = attr.ib(repr=False, default=None)


@attr.s
class Example(object):
    """
    Single example.
    """
    value       = attr.ib()
    name        = attr.ib(default=None)
    description = attr.ib(default=None, repr=False)
    displayName = attr.ib(default=None)

    # Not sure when validation of examples should get done; leave for now.
    strict      = attr.ib(default=True)


@attr.s
class DataTypeAttrs(object):
    """
    Mixin to add properties to BaseDataType that is not a part of the RAML
    spec.
    """
    raw          = attr.ib(repr=False, cmp=False)
    raml_version = attr.ib(repr=False)
    root         = attr.ib(repr=False)
    errors       = attr.ib(repr=False, cmp=False)
    config       = attr.ib(repr=False)


@attr.s
class BaseDataType(RAMLDataType, DataTypeAttrs):
    """
    Base class for all data types.
    """


@type_class("object")
@attr.s
class ObjectDataType(BaseDataType):
    """
    Type class for RAML object data types.
    """
    properties            = attr.ib(repr=False, default=None,
                                    convert=parse_properties)
    min_properties        = attr.ib(repr=False, default=0)
    max_properties        = attr.ib(repr=False, default=None)
    additional_properties = attr.ib(repr=False, default=True)
    discriminator         = attr.ib(repr=False, default=None)
    # TODO: validate based on if discriminator is set in type declaration
    discriminator_value   = attr.ib(repr=False, default=None,
                                    validator=discriminator_value)


@attr.s
class ArrayDataType(BaseDataType):
    """
    Type class for RAML array data types.
    """
    items        = attr.ib(repr=False, default=None)
    unique_items = attr.ib(repr=False, default=False)
    min_items    = attr.ib(repr=False, default=0, convert=int)
    max_items    = attr.ib(repr=False, default=RAML_MAX_INT, convert=int)


@attr.s
class BaseScalarDataType(BaseDataType):
    pass


@attr.s
class ScalarDataType(BaseDataType):
    """
    Type class for RAML scalar data types.
    """
    enum = attr.ib(repr=False, default=None)


# TODO: try to move inside of StringDataType
def create_re(pattern):
    if not pattern:
        return None
    return re.compile(pattern)


# <-- Scalar Types -->
@type_class("string")
@attr.s
class StringDataType(ScalarDataType):
    """
    Type class for RAML string data types.
    """
    pattern    = attr.ib(repr=False, default=None, convert=create_re)
    # TODO: validate if int & if positive
    min_length = attr.ib(repr=False, default=0, convert=int)
    # TODO: validate if int and if positive
    max_length = attr.ib(repr=False, default=RAML_MAX_INT, convert=int)


@type_class("number")
@attr.s
class NumberDataType(ScalarDataType):
    """
    Type class for RAML number data types (JSON number).
    """
    # TODO: Validate according to valid values:
    # int32, int64, int, long, float, double, int16, int8
    format      = attr.ib(repr=False, default="int")
    # TODO: convert based on `format`
    minimum     = attr.ib(repr=False, default=None)
    maximum     = attr.ib(repr=False, default=None)
    multiple_of = attr.ib(repr=False, default=None)


@type_class("integer")
@attr.s
class IntegerDataType(NumberDataType):
    """
    Type class for RAML integer data types (JSON number)
    """
    # TODO: add validation that the value given is an int


@type_class("boolean")
@attr.s
class BooleanDataType(ScalarDataType):
    """
    Type class for RAML boolean data types (JSON boolean)
    """
    # TODO: validation?


@attr.s
class DateDataType(ScalarDataType):
    """
    Type class for RAML date data types.
    """
    # TODO: inherit/overwrite `type` from BaseDataType, and
    # validate according to valid values:
    # date-only, time-only, datetime-only, datetime
    # TODO: perhaps convert by valid values


@attr.s
class FileDataType(BaseScalarDataType):
    """
    Type class for RAML file data types.
    """
    # TODO: validate on valid content-type strings
    file_type = attr.ib(repr=False, default=None)
    # TODO: validate if int & if positive
    min_length = attr.ib(repr=False, default=0, convert=int)
    # TODO: validate if int and if positive
    max_length = attr.ib(repr=False, default=RAML_MAX_INT, convert=int)


@attr.s
class NullDataType(ScalarDataType):
    """
    Type class for RAML null data.
    """
    # TODO: see https://github.com/raml-org/raml-spec/blob/master/versions/raml-10/raml-10.md/#null-type  # NOQA


# </-- Scalar Types -->
