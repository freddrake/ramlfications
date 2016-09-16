# -*- coding: utf-8 -*-
# Copyright (c) 2016 Spotify AB

from __future__ import absolute_import, division, print_function

from six import iteritems

from ramlfications.errors import UnknownDataTypeError
from ramlfications.models import RAML_DATA_TYPES, STANDARD_RAML_TYPES
from ramlfications.models.data_types import Example
from .common import merge_dicts
from .parser import convert_camel_case


def _resolve_type(declared_type, raw, root):
    raw_data = root.raw
    raw_types = raw_data.get("types", {})
    inherited = [{t: v} for t, v in iteritems(raw_types) if t == declared_type]
    return merge_dicts(raw, inherited[0].get(declared_type))


def parse_type(name, raw, root):
    declared_type = raw.get("type", "string")

    # TODO: prob want better logic than just grabbing the first one
    if isinstance(declared_type, list):
        declared_type = declared_type[0]

    # TODO: maybe move this error checking into validation
    try:
        data_type_cls = RAML_DATA_TYPES[declared_type]
    except KeyError:
        msg = ("'{0}' is not a supported or defined RAML Data "
               "Type.".format(declared_type))
        raise UnknownDataTypeError(msg)

    # update the RAML_DATA_TYPES so we can inherit it if needed
    if name not in RAML_DATA_TYPES:
        RAML_DATA_TYPES[name] = data_type_cls
    if declared_type not in STANDARD_RAML_TYPES:
        # TODO: clean up - need more graceful logic other than
        # grabbing types again and iterating
        declared_type = raw.get("type", "string")
        if isinstance(declared_type, list):
            for d in declared_type:
                raw = _resolve_type(d, raw, root)
        else:
            raw = _resolve_type(declared_type, raw, root)

    data = dict([(convert_camel_case(k), v) for k, v in iteritems(raw)])
    data["raw"] = raw
    data["name"] = name
    data["root"] = root
    data["description"] = raw.get("description")
    data["raml_version"] = root.raml_version
    data["display_name"] = raw.get("displayName", name)
    # TODO: what to do when it's a list?
    data["type"] = declared_type

    # TODO: super hacky, fixme
    if declared_type == "string":
        # TODO: prob want to clean this up, too
        try:
            data.pop("properties")
        except KeyError:
            pass

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
