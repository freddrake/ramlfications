# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
"""\
Tests for handling of data type examples in RAML 0.8.

"""

import os
import pytest

from ramlfications.parser import parse_raml
from ramlfications.config import setup_config
from ramlfications.utils import load_file

from tests.base import V020EXAMPLES


@pytest.fixture(scope="session")
def api():
    ramlfile = os.path.join(V020EXAMPLES, "data_types_0_8.raml")
    loaded_raml = load_file(ramlfile)
    conffile = os.path.join(V020EXAMPLES, "test_config.ini")
    config = setup_config(conffile)
    return parse_raml(loaded_raml, config)


def get_form_param(api, resource, name="key"):
    res, = api.resources.filter_by(name=resource)
    fp, = res.body[0].form_params.filter_by(name=name)
    return fp


def test_examples_ignored(api):
    fp = get_form_param(api, "/with_example_and_examples")
    assert fp.example == "This is the example."


def xxxx_multiple_types(api):
    # Not yet supported.
    fp = get_form_param(api, "/with_example_and_examples", "multityped")


def test_simple_example_structured(api):
    #
    # If an example is presented as a YAML map with a value key, that's
    # just part of the value, since RAML 0.8 doesn't have any notion of
    # annotations or other facets of an example other than the value.
    #
    fp = get_form_param(api, "/with_example_structured")
    assert fp.example == {"value": "This whole map is a value."}


def test_simple_example_unstructured(api):
    fp = get_form_param(api, "/with_example_unstructured")
    assert fp.example == "This is a value."


def test_header_with_example(api):
    h = api.resources.filter_by(name="/with_header")[0].headers[0]
    assert h.example is True


def test_base_uri_param(api):
    p = api.base_uri_params[0]
    assert p.description.raw == "account name"
    assert p.example == "splat"
    assert p.type == "string"


def test_query_param(api):
    res = api.resources.filter_by(name="/with_example_and_examples")[0]
    p = res.query_params.filter_by(name="cached")[0]
    assert p.description.raw == "Allow cached data?"
    assert p.example is False
    assert p.type == "boolean"


def test_uri_param(api):
    res = api.resources.filter_by(name="/with_uri_param/{id}")[0]
    p = res.uri_params[0]
    assert p.description is None
    assert p.example == "s234gs9"
    assert p.type == "string"
