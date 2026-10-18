"""Parser registry: new artifact types plug in here without touching the pipeline."""
from __future__ import annotations

from . import component as _component  # noqa: F401
from . import eca as _eca  # noqa: F401
from . import entity as _entity  # noqa: F401
from . import gradle_controller as _gradle_controller  # noqa: F401
from . import service as _service  # noqa: F401

PARSERS = {
    "component": _component.parse,
    "service": _service.parse,
    "entity": _entity.parse,
    "eca": _eca.parse,
    "controller": _gradle_controller.parse_controller,
    "gradle": _gradle_controller.parse_gradle,
}
