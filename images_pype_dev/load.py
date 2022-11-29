"""prompt loader"""
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from markata.hookspec import hook_impl, register_attr

# source env variables
load_dotenv()


@dataclass
class Article:
    file: Path

    def __post_init__(self):

        self.published = True
        self.title = self.file.name
        self.slug = self.file.name.replace(",", "-").replace(".", "-").replace(" ", "-")

    def __getitem__(self, key, default):
        return self.to_dict().get(key, default)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def keys(self):
        return self.to_dict().keys()

    def to_dict(self):
        return vars(self)

    def get(self, key, default=None):
        return self.__getitem__(key, default)

    def delete(self):
        self.file.unlink()


@hook_impl
def configure(markata) -> None:
    markata.content_directories = [Path("static")]


# def _turn_original_png_path_to_static_webp_path(filepath: str):

#     return Path("static", Path(Path(filepath).name)).with_suffix(".webp")


@hook_impl
@register_attr("articles")
def load(markata) -> None:
    markata.articles = []
    images = (
        # regardless of which suboutput folder the source images are in, I store them flat in static - so just check for the webp version of the picture in this repo
        Path("static", Path(Path(image).name).with_suffix(".webp"))
        for image in Path("./static").glob("**/*.png")
    )

    markata.articles += [Article(image) for image in images]
