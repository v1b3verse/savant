"""Tests for pysavant.services.shade."""

import pytest

from pysavant.protocol import SVC_ENV_SHADE
from pysavant.services.shade import set_level, stop


class TestShade:
    def test_set_level(self):
        req = set_level("Living Room", 50)
        assert req.service_type == SVC_ENV_SHADE
        assert req.request == "__SetShadeLevel"
        assert req.request_args == {"ShadeLevel": 50}

    def test_set_level_bounds(self):
        set_level("z", 0)
        set_level("z", 100)

    def test_set_level_invalid(self):
        with pytest.raises(ValueError):
            set_level("z", -1)
        with pytest.raises(ValueError):
            set_level("z", 101)

    def test_logical_component(self):
        req = set_level("Living Room", 50)
        assert req.logical_component == "Lighting_controller"

    def test_stop(self):
        req = stop("Living Room")
        assert req.request == "__ShadeStop"
        assert req.logical_component == "Lighting_controller"
