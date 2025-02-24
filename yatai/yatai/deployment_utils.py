import logging

from .exceptions import YataiDeploymentException
from .proto.deployment_pb2 import Deployment, DeploymentSpec
from .utils.ruamel_yaml import YAML

logger = logging.getLogger(__name__)

SPEC_FIELDS_AVAILABLE_FOR_UPDATE = ["bento_name", "bento_version"]

SAGEMAKER_FIELDS_AVAILABLE_FOR_UPDATE = [
    "api_name",
    "instance_type",
    "instance_count",
    "num_of_gunicorn_workers_per_instance",
]


def deployment_dict_to_pb(deployment_dict):
    deployment_pb = Deployment()
    if deployment_dict.get("spec"):
        spec_dict = deployment_dict.get("spec")
    else:
        raise YataiDeploymentException('"spec" is required field for deployment')
    platform = spec_dict.get("operator")
    if platform is not None:
        # converting platform parameter to DeploymentOperator name in proto
        # e.g. 'aws-lambda' to 'AWS_LAMBDA'
        deployment_pb.spec.operator = DeploymentSpec.DeploymentOperator.Value(
            platform.replace("-", "_").upper()
        )

    for field in ["name", "namespace"]:
        if deployment_dict.get(field):
            deployment_pb.__setattr__(field, deployment_dict.get(field))
    if deployment_dict.get("labels") is not None:
        deployment_pb.labels.update(deployment_dict.get("labels"))
    if deployment_dict.get("annotations") is not None:
        deployment_pb.annotations.update(deployment_dict.get("annotations"))

    if spec_dict.get("bento_name"):
        deployment_pb.spec.bento_name = spec_dict.get("bento_name")
    if spec_dict.get("bento_version"):
        deployment_pb.spec.bento_version = spec_dict.get("bento_version")

    return deployment_pb


def deployment_yaml_string_to_pb(deployment_yaml_string):
    yaml = YAML()
    deployment_yaml = yaml.load(deployment_yaml_string)
    return deployment_dict_to_pb(deployment_yaml)
