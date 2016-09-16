# -*- coding: utf-8 -*-
# Copyright (c) 2016 Spotify AB

from __future__ import absolute_import, division, print_function

from six import iteritems

from ramlfications.errors import UnknownDataTypeError
from ramlfications.models import RAML_DATA_TYPES
from ramlfications.models.data_types import Example
from .parser import convert_camel_case


def parse_type(name, raw, root):
    declared_type = raw.get("type", "string")
    # TODO: maybe move this error checking into validation
    try:
        data_type_cls = RAML_DATA_TYPES[declared_type]
    except KeyError:
        msg = ("'{0}' is not a supported or defined RAML Data "
               "Type.".format(declared_type))
        raise UnknownDataTypeError(msg)

    data = dict([(convert_camel_case(k), v) for k, v in iteritems(raw)])
    data["raw"] = raw
    data["name"] = name
    data["root"] = root
    data["description"] = raw.get("description")
    data["raml_version"] = root.raml_version
    data["display_name"] = raw.get("displayName", name)

    if root.raml_version == "0.8" and "examples" in data:
        del data["examples"]

    if 'example' in raw:
        if root.raml_version == "0.8":
            example = Example(value=raw["example"])
        else:
            example = parse_example(root, None, raw['example'])
        data['example'] = example

    if 'examples' in raw and root.raml_version >= "1.0":
        if "example" in data:
            raise RuntimeError("example and examples cannot co-exist")
        examples = raw['examples']
        # Must be a map:
        if not isinstance(examples, dict):
            # Need to decide what exception to make this.
            raise UnknownDataTypeError
        data['examples'] = [parse_example(root, nm, val)
                            for nm, val in iteritems(examples)]

    return data_type_cls(**data)


def parse_example(root, name, node):
    data = dict(name=name, value=node)
    if isinstance(node, dict):
        # Might have a 'value' key; adds a layer.
        if "value" in node:
            data = node
            node["name"] = name

    return Example(**data)
