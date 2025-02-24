# # APIS in utils:
# lock_pypi_versions
# with_pip_install_options
# conda_environment
# ImageProvider

import logging
import re
import sys
import typing as t

from simple_di import Provide, inject

from ._internal.configuration.containers import BentoMLContainer

logger = logging.getLogger(__name__)

SUPPORTED_PYTHON_VERSION: t.List = ["3.6", "3.7", "3.8"]
SUPPORTED_BASE_DISTROS: t.List = ["slim", "centos7", "centos8"]
SUPPORTED_GPU_DISTROS: t.List = SUPPORTED_BASE_DISTROS

SUPPORTED_RELEASES_COMBINATION: t.Dict[str, t.List[str]] = {
    "cudnn": SUPPORTED_BASE_DISTROS,
    "devel": SUPPORTED_BASE_DISTROS,
    "runtime": SUPPORTED_BASE_DISTROS + ["ami2", "alpine3.14"],
}

SEMVER_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)?$")

BACKWARD_COMPATIBILITY_WARNING: str = """\
Since 1.0.0, we changed the format of docker tags, thus {classname}
will only supports image tag from 1.0.0 forward, while detected bentoml_version
is {bentoml_version}.
Refers to https://hub.docker.com/r/bentoml/model-server/
if you need older version of bentoml. Using default devel image instead...
"""  # noqa: E501


class ImageProvider(object):
    """
    BentoML-provided docker images.

    Args:
        distros (string): distro that will be used for docker image.
        python_version (string): python version for given docker image.
        gpu (bool): Optional GPU supports.
        bentoml_version (string): Optional bentoml_version.

    Raises:
         RuntimeError: ``bentoml_version`` doesn't \
                        match semantic versioning
         RuntimeError: ``python_version`` and ``distros`` \
                        is not yet supported by BentoML
         RuntimeError: invalid combination of supported GPU distros.

    Returns:

        .. code-block:: shell

            bentoml/model-server:<release_type>-<python_version>-<distros>-<suffix>

            # suffix: runtime or cudnn
            # distros: formatted <distro><version> (ami2, centos8, centos7)
            # python_version: 3.7,3.8
            # release_type: devel or versioned (0.14.0)

        Example results:

        * bentoml/model-server:`devel-python3.7-slim`
        * bentoml/model-server:`0.14.0-python3.8-centos8-cudnn`
        * bentoml/model-server:`0.14.0-python3.7-ami2-runtime`


    Example::

    import bentoml
    from bentoml.docker import ImageProvider
    from bentoml.frameworks.pytorch import PyTorchModel
    from pandas import DataFrame

    @bentoml.env(docker_base_image=ImageProvider('debian', '3.8', gpu=True))
    @bentoml.artifacts([PyTorchModel('net')])
    class Service(bentoml.BentoService):
        @bentoml.api()
        def predict(self, df: DataFrame):
            return self.net.predict(df)
    """

    # fmt: off
    _release_fmt: t.ClassVar[str] = "bentoml/model-server:{release_type}-python{python_version}-{distros}{suffix}"  # noqa: E501 # pylint: disable=line-too-long

    _singleton: t.ClassVar[t.Optional["ImageProvider"]] = None
    # fmt: on

    @inject  # type: ignore
    def __init__(
        self,
        distros: str,
        gpu: bool = False,
        python_version: t.Optional[str] = None,
        bentoml_version: t.Optional[str] = Provide[
            BentoMLContainer.bento_bundle_deployment_version
        ],
    ) -> None:
        if bentoml_version:
            major, minor, patch = bentoml_version.split(".")
            if not SEMVER_REGEX.match(bentoml_version):
                raise ValueError(
                    f"{bentoml_version} doesn't follow semantic versioning."
                )
            if not patch:
                raise ValueError(
                    f"{bentoml_version} pass semver check but have incorrect format."
                )
            # we only support the new format with 0.14.0 forward
            if int(major) == 0 and int(minor) <= 13:
                msg = BACKWARD_COMPATIBILITY_WARNING.format(
                    classname=self.__class__.__name__, bentoml_version=bentoml_version,
                )
                logger.warning(msg)
                self._release_type: str = "devel"
            else:
                self._release_type = bentoml_version

        # fmt: off
        self._suffix: str = '-' + self.get_suffix(gpu) if self._release_type != 'devel' else ''  # noqa: E501

        # fmt: on
        if python_version:
            _py_ver: str = python_version
        else:
            _py_ver = ".".join(map(str, sys.version_info[:2]))
            logger.warning(
                f"No python_version is specified, using {_py_ver}. "
                f"List of supported python version: {SUPPORTED_PYTHON_VERSION}. "
                "If your python_version isn't supported make sure to specify, e.g: "
                "bentoml.docker.ImageProvider('centos7', python_version='3.6')"
            )
        if _py_ver not in SUPPORTED_PYTHON_VERSION:
            raise RuntimeError(
                f"{python_version} is not supported. "
                f"Supported Python version: {SUPPORTED_PYTHON_VERSION}"
            )

        self._python_version: str = _py_ver

        if "ubuntu" in distros or "debian" in distros:
            logger.debug("Using slim tags for debian based distros")
            _distros = "slim"
        elif "amazon" in distros:
            logger.debug("Convert amazonlinux tags to ami2")
            _distros = "ami2"
        else:
            _distros = distros

        if gpu and _distros not in SUPPORTED_GPU_DISTROS:
            raise RuntimeError(
                f"{_distros} with GPU={gpu} is forbidden. "
                f"GPU-supported distros: {SUPPORTED_GPU_DISTROS} "
            )

        if (
            _distros not in SUPPORTED_RELEASES_COMBINATION["devel"]
            and self._release_type == "devel"
        ):
            raise RuntimeError(f"{distros} doesn't support devel tags.")

        if _distros not in SUPPORTED_RELEASES_COMBINATION[self.get_suffix(gpu)]:
            raise RuntimeError(
                f"{_distros} is not yet supported. "
                "Supported distros: "
                f"{SUPPORTED_RELEASES_COMBINATION[self.get_suffix(gpu)]}"
            )

        self._distros: str = _distros

    @staticmethod
    def get_suffix(gpu: bool) -> str:
        return "runtime" if not gpu else "cudnn"

    def __repr__(self: "ImageProvider") -> str:
        return self._release_fmt.format(
            release_type=self._release_type,
            python_version=self._python_version,
            distros=self._distros,
            suffix=self._suffix,
        )
