import os
import typing as t

from ._internal.models.base import MODEL_NAMESPACE, Model
from ._internal.types import MetadataType, PathType
from .exceptions import MissingDependencyException

try:
    import mxnet  # pylint: disable=unused-import
    from mxnet import gluon
except ImportError:
    raise MissingDependencyException("mxnet is required by GluonModel")


class GluonModel(Model):
    """
    Model class for saving/loading :obj:`mxnet.gluon` models

    Args:
        model (`mxnet.gluon.Block`):
            Every :obj:`mxnet.gluon` object is based on :obj:`mxnet.gluon.Block`
        metadata (`Dict[str, Any]`,  `optional`, default to `None`):
            Class metadata

    Raises:
        MissingDependencyException:
            :obj:`mxnet` is required by GluonModel

    Example usage under :code:`train.py`::

        TODO:

    One then can define :code:`bento.py`::

        TODO:
    """

    def __init__(
        self, model: "mxnet.gluon.Block", metadata: t.Optional[MetadataType] = None,
    ):
        super(GluonModel, self).__init__(model, metadata=metadata)

    @classmethod
    def load(cls, path: PathType) -> "mxnet.gluon.Block":
        json_path: str = os.path.join(path, f"{MODEL_NAMESPACE}-symbol.json")
        params_path: str = os.path.join(path, f"{MODEL_NAMESPACE}-0000.params")
        return gluon.nn.SymbolBlock.imports(json_path, ["data"], params_path)

    def save(self, path: PathType) -> None:
        self._model.export(os.path.join(path, MODEL_NAMESPACE))
