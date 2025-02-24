import os
import shutil
import typing as t

from ._internal.models.base import MODEL_NAMESPACE, Model
from ._internal.types import MetadataType, PathType
from .exceptions import BentoMLException, MissingDependencyException

try:
    import onnx
    import onnxruntime
except ImportError:
    raise MissingDependencyException('"onnx" package is required by ONNXModel')


class ONNXModel(Model):
    """
    Model class for saving/loading :obj:`onnx` models.

    Args:
        model (`str`):
            Given filepath or protobuf of converted model.
            Make sure to use corresponding library to convert
            model from different frameworks to ONNX format.
        backend (`str`, `optional`, default to `onnxruntime`):
            Name of ONNX inference runtime. ["onnxruntime", "onnxruntime-gpu"]
        metadata (`Dict[str, Any]`,  `optional`, default to `None`):
            Class metadata.

    Raises:
        MissingDependencyException:
            :obj:`onnx` is required by ONNXModel
        NotImplementedError:
            :obj:`backend` as onnx runtime is not supported by ONNX
        BentoMLException:
            :obj:`backend` as onnx runtime is not supported by ONNXModel
        InvalidArgument:
            :obj:`path` passed in :meth:`~save` is not either
             a :obj:`onnx.ModelProto` or filepath

    Example usage under :code:`train.py`::

        TODO:

    One then can define :code:`bento.py`::

        TODO:
    """

    SUPPORTED_ONNX_BACKEND: t.List[str] = ["onnxruntime", "onnxruntime-gpu"]
    ONNX_EXTENSION: str = ".onnx"

    def __init__(
        self,
        model: t.Union[PathType, onnx.ModelProto],
        backend: t.Optional[str] = "onnxruntime",
        metadata: t.Optional[MetadataType] = None,
    ):
        super(ONNXModel, self).__init__(model, metadata=metadata)
        if backend not in self.SUPPORTED_ONNX_BACKEND:
            raise BentoMLException(
                f'"{backend}" runtime is currently not supported for ONNXModel'
            )
        self._backend = backend

    @classmethod
    def __get_model_fpath(cls, path: PathType) -> PathType:
        return os.path.join(path, f"{MODEL_NAMESPACE}{cls.ONNX_EXTENSION}")

    @classmethod
    def load(
        cls, path: t.Union[PathType, onnx.ModelProto]
    ) -> "onnxruntime.InferenceSession":
        if isinstance(path, onnx.ModelProto):
            return onnxruntime.InferenceSession(path.SerializeToString())
        else:
            _get_path = str(cls.__get_model_fpath(path))
            return onnxruntime.InferenceSession(_get_path)

    def save(self, path: t.Union[PathType, "onnx.ModelProto"]) -> None:
        if isinstance(self._model, onnx.ModelProto):
            onnx.save_model(self._model, self.__get_model_fpath(path))
        else:
            shutil.copyfile(self._model, str(self.__get_model_fpath(path)))
