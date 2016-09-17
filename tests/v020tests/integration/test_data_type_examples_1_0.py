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
    ramlfile = os.path.join(V020EXAMPLES, "data_types_1_0.raml")
    loaded_raml = load_file(ramlfile)
    conffile = os.path.join(V020EXAMPLES, "test_config.ini")
    config = setup_config(conffile)
    return parse_raml(loaded_raml, config)
