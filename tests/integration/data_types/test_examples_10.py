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

from tests.base import RAML_10


@pytest.fixture(scope="session")
def api():
    ramlfile = os.path.join(RAML_10, "data-type-examples.raml")
    loaded_raml = load_file(ramlfile)
    conffile = os.path.join(RAML_10, "test_config.ini")
    config = setup_config(conffile)
    return parse_raml(loaded_raml, config)


def get_resource_body_type(api, resource):
    res, = api.resources.filter_by(name=resource)
    return res.body[0].type


def get_named_type(api, name):
    t, = api.types.filter_by(name=name)
    return t


def test_simple_example_structured(api):
    t = get_named_type(api, "with_example_structured")
    assert t.examples is None

    ex = t.example
    assert ex.description.raw == "This is a typical structure."
    assert ex.display_name.raw == "Typical Example"
    assert ex.strict is True
    assert ex.value == {"key": "Yo."}


def test_simple_example_unstructured(api):
    t = get_named_type(api, "with_example_unstructured")
    assert t.examples is None

    ex = t.example
    assert ex.description is None
    assert ex.display_name is None
    assert ex.strict is True
    assert ex.value == {"key": "Example value."}


def test_multiple_examples(api):
    t = get_named_type(api, "with_multiple_examples")
    assert t.example is None
    assert len(t.examples) == 3

    ex, = t.examples.filter_by(name="simple")
    assert ex.description is None
    assert ex.display_name.raw == "simple"
    assert ex.strict is True
    assert ex.value == "abc"

    ex, = t.examples.filter_by(name="fancy")
    assert ex.description is None
    assert ex.display_name.raw == "fancy"
    assert ex.strict is True
    assert ex.value == "two words"

    ex, = t.examples.filter_by(name="excessive")
    assert ex.description.raw == "There's way too much text here.\n"
    assert ex.display_name.raw == "Serious Overkill"
    assert ex.strict is False
    assert ex.value == {"error": "This should not be a map."}


def test_header_with_example(api):
    h = api.resources.filter_by(name="/with_header")[0].headers[0]
    assert h.name == "x-extra-fluff"
    assert h.example is True


def test_header_with_mutiple_examples(api):
    h = api.resources.filter_by(name="/with_header")[0].headers[1]
    assert h.name == "x-multiple"
    assert h.example is None
    assert len(h.examples) == 4

    ex, = h.examples.filter_by(name="simple")
    assert ex.description is None
    assert ex.display_name.raw == "simple"
    assert ex.strict is True
    assert ex.value == "42"

    ex, = h.examples.filter_by(name="typical")
    assert ex.description.raw == "This is what we expect."
    assert ex.display_name.raw == "Typical Value"
    assert ex.strict is True
    assert ex.value == "typical"

    ex, = h.examples.filter_by(name="special")
    assert ex.description.raw == "No one expects the ..."
    assert ex.display_name.raw == "Surprise Visit"
    assert ex.strict is True
    assert ex.value == "Spanish Inqusition!"

    ex, = h.examples.filter_by(name="broken")
    assert ex.description.raw == "Send this for a 500"
    assert ex.display_name.raw == "DON'T DO THIS"
    assert ex.strict is False
    assert ex.value == "breakfast"
