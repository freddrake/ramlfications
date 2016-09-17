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


def test_08_examples_ignored(api):
    t, = api.types.filter_by(name="with_example_and_examples")
    assert t.example == "This is the example."
    assert t.examples is None


def test_08_simple_example_structured(api):
    #
    # If an example is presented as a YAML map with a value key, that's
    # just part of the value, since RAML 0.8 doesn't have any notion of
    # annotations or other facets of an example other than the value.
    #
    t, = api.types.filter_by(name="with_example_structured")
    assert t.example == {"value": "This is a value."}
    assert t.examples is None


def test_08_simple_example_unstructured(api):
    t, = api.types.filter_by(name="with_example_unstructured")
    assert t.example == "This is a value."
    assert t.examples is None
