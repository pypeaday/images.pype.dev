from string import Template
from pathlib import Path

with open("template/index.html") as f:
    index_template = Template(f.read())
with open("template/image.html") as f:
    image_template = Template(f.read())
with open("template/video.html") as f:
    video_template = Template(f.read())


items = [*list(Path("static/thumb").glob("*")), *list(Path("static").glob("*.webm"))]
items.sort()


def render(filepath):
    if filepath.suffix == ".webm":
        return video_template.safe_substitute(file=filepath.stem)
    return image_template.safe_substitute(file=filepath.name)


images = "".join([render(filepath) for filepath in items])

index = index_template.safe_substitute(images=images)

with open("static/index.html", "w+") as f:
    f.write(index)
