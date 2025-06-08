# images-pype-dev

Image repo for [pype.dev](https://www.pype.dev)

## Shotput WebUI

`uv run app/shotput.py` to start an app that you can paste screenshots in and get
back a markdown link to serve the image up on the rendered post via
statically.io through the github repo

### Setup

1. if using SSH then setup an ssh key with github and mount it into the container at `/home/appuser/.ssh/id_rsa:ro`
2. update `ssh_config` if you have any host mappings to consider
3. `docker compose up` to use docker, or `uv run app/shotput.py` to use uvicorn

### Configuration

See [app/config.toml](./app/config.toml)


### Example

![20250607130609_dadd33eb.png](https://cdn.statically.io/gh/pypeaday/images.pype.dev/main/blog-media/20250607130609_dadd33eb.png)

pasting an image let's you copy the markdown link for easy pasting

```markdown
![20250607130609_dadd33eb.png](https://cdn.statically.io/gh/pypeaday/images.pype.dev/main/blog-media/20250607130609_dadd33eb.png)
```

## License

`images-pype-dev` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
