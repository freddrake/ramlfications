# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
"""\
Tests for handling of data type examples.

"""

import os
import pytest

from ramlfications.parser import parse_raml
from ramlfications.config import setup_config
from ramlfications.utils import load_file

from tests.base import V020EXAMPLES


def _loaded_raml(name):
    ramlfile = os.path.join(V020EXAMPLES, name)
    loaded_raml = load_file(ramlfile)
    conffile = os.path.join(V020EXAMPLES, "test_config.ini")
    config = setup_config(conffile)
    return parse_raml(loaded_raml, config)


@pytest.fixture(scope="session")
def api08():
    return _loaded_raml("data_types_0_8.raml")


@pytest.fixture(scope="session")
def api10():
    return _loaded_raml("data_types_1_0.raml")


def test_08_examples_ignored(api08):
    t, = api08.types.filter_by(name="with_example_and_examples")
    ex = t.example

    assert ex.value == "This is the example."
    assert ex.name is None
    assert ex.displayName is None
    assert ex.description is None
    assert ex.strict is True

    assert t.examples is None
