"""json load plugin"""
from typing import TYPE_CHECKING

import requests

from markata.hookspec import hook_impl

if TYPE_CHECKING:
    from markata import Markata


@hook_impl
def load(markata: "Markata") -> None:
    markata.articles = requests.get(markata.config["glob_json"]["url"]).json()[
        "articles"
    ]
    # use for testing a single image
    # markata.articles = [a for a in markata.articles if "zev" in a["title"].lower()]
