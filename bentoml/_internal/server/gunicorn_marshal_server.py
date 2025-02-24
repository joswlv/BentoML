import logging
from typing import TYPE_CHECKING

from gunicorn.app.base import Application
from simple_di import Provide, inject

from ..configuration.containers import BentoMLContainer

marshal_logger = logging.getLogger("bentoml.marshal")


if TYPE_CHECKING:  # make type checkers happy
    from bentoml._internal.marshal.marshal import MarshalApp


class GunicornMarshalServer(Application):  # pylint: disable=abstract-method
    @inject(squeeze_none=True)
    def __init__(
        self,
        *,
        workers: int = Provide[BentoMLContainer.config.bento_server.microbatch.workers],
        timeout: int = Provide[BentoMLContainer.config.bento_server.timeout],
        max_request_size: int = Provide[
            BentoMLContainer.config.bento_server.max_request_size
        ],
        host: str = Provide[BentoMLContainer.service_host],
        port: int = Provide[BentoMLContainer.service_port],
        loglevel: str = Provide[BentoMLContainer.config.bento_server.logging.level],
    ):
        self.port = port
        self.options = {
            "bind": "%s:%s" % (host, port),
            "timeout": timeout,
            "limit_request_line": max_request_size,
            "loglevel": loglevel.upper(),
            "worker_class": "aiohttp.worker.GunicornWebWorker",
        }
        if workers:
            self.options["workers"] = workers
        super().__init__()

    def load_config(self):
        self.load_config_from_file("python:bentoml.server.gunicorn_config")

        # override config with self.options
        assert self.cfg, "gunicorn config must be loaded"
        for k, v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                self.cfg.set(k.lower(), v)

    @property
    @inject
    def app(self, app: "MarshalApp" = Provide[BentoMLContainer.proxy_app]):
        return app

    def load(self):
        return self.app.get_app()

    def run(self):
        marshal_logger.info("Running micro batch service on :%d", self.port)
        super().run()
