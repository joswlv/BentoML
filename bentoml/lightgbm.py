import os
import typing as t

from ._internal.models.base import MODEL_NAMESPACE, TXT_EXTENSION, Model
from ._internal.types import MetadataType, PathType
from .exceptions import MissingDependencyException

try:
    import lightgbm
except ImportError:
    raise MissingDependencyException("lightgbm is required by LightGBMModel")


class LightGBMModel(Model):
    """
    Model class for saving/loading :obj:`lightgbm` models

    Args:
        model (`lightgbm.Booster`):
            LightGBM model instance is of type :class:`lightgbm.Booster`
        metadata (`Dict[str, Any]`,  `optional`, default to `None`):
            Class metadata

    Raises:
        MissingDependencyException:
            :obj:`lightgbm` is required by LightGBMModel

    Example usage under :code:`train.py`::

        TODO:

    One then can define :code:`bento.py`::

        TODO:
    """

    def __init__(
        self, model: "lightgbm.Booster", metadata: t.Optional[MetadataType] = None,
    ):
        super(LightGBMModel, self).__init__(model, metadata=metadata)

    @classmethod
    def load(cls, path: PathType) -> "lightgbm.Booster":
        return lightgbm.Booster(
            model_file=os.path.join(path, f"{MODEL_NAMESPACE}{TXT_EXTENSION}")
        )

    def save(self, path: PathType) -> None:
        self._model.save_model(os.path.join(path, f"{MODEL_NAMESPACE}{TXT_EXTENSION}"))
