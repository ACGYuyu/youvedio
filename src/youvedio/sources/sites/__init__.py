"""Site parser registry — auto-discovered by importlib."""

from youvedio.sources.sites.acgrip import AcgRipParser
from youvedio.sources.sites.anidex import AnidexParser
from youvedio.sources.sites.base import SiteParser
from youvedio.sources.sites.dmhy import DmhyParser
from youvedio.sources.sites.mikan import MikanParser
from youvedio.sources.sites.nyaa import NyaaParser
from youvedio.sources.sites.tokyotosho import TokyoToshoParser
from youvedio.sources.sites.x1337 import X1337Parser

__all__ = [
    "SiteParser",
    "NyaaParser",
    "DmhyParser",
    "MikanParser",
    "X1337Parser",
    "AcgRipParser",
    "AnidexParser",
    "TokyoToshoParser",
]
