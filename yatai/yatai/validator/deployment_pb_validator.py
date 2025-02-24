# Copyright 2019 Atalaya Tech, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cerberus import Validator

from bentoml._internal.utils import ProtoMessageToDict

from ..db.stores.label import _validate_labels
from ..exceptions import InvalidArgument
from ..proto.deployment_pb2 import DeploymentSpec, DeploymentState

deployment_schema = {
    "name": {"type": "string", "required": True, "minlength": 4},
    # namespace is optional - YataiService will fill-in the default namespace configured
    # when it is missing in the apply deployment request
    "namespace": {"type": "string", "required": False, "minlength": 3},
    "labels": {"type": "dict", "deployment_labels": True},
    "annotations": {"type": "dict", "allow_unknown": True},
    "created_at": {"type": "string"},
    "last_updated_at": {"type": "string"},
    "spec": {
        "type": "dict",
        "required": True,
        "schema": {
            "operator": {
                "type": "string",
                "required": True,
                "allowed": DeploymentSpec.DeploymentOperator.keys(),
            },
            "bento_name": {"type": "string", "required": True},
            "bento_version": {
                "type": "string",
                "required": True,
                "bento_service_version": True,
            },
            "custom_operator_config": {
                "type": "dict",
                "schema": {
                    "name": {"type": "string"},
                    "config": {"type": "dict", "allow_unknown": True},
                },
            },
        },
    },
    "state": {
        "type": "dict",
        "schema": {
            "state": {"type": "string", "allowed": DeploymentState.State.keys()},
            "error_message": {"type": "string"},
            "info_json": {"type": "string"},
            "timestamp": {"type": "string"},
        },
    },
}


class YataiDeploymentValidator(Validator):
    def _validate_bento_service_version(self, bento_service_version, field, value):
        """ Test the given BentoService version is not "latest"

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if bento_service_version and value.lower() == "latest":
            self._error(
                field,
                'Must use specific "bento_version" in deployment, using "latest" is '
                "an anti-pattern.",
            )

    def _validate_deployment_labels(self, deployment_labels, field, value):
        """ Test label key value schema

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        if deployment_labels:
            try:
                _validate_labels(value)
            except InvalidArgument:
                self._error(
                    field,
                    "Valid label key and value must be 63 characters or less and "
                    "must be being and end with an alphanumeric character "
                    "[a-z0-9A-Z] with dashes (-), underscores (_), and dots (.)",
                )


def validate_deployment_pb(pb):
    pb_dict = ProtoMessageToDict(pb)
    v = YataiDeploymentValidator(deployment_schema)
    if v.validate(pb_dict):
        return None
    else:
        return v.errors
