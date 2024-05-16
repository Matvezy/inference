from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union

from pydantic import AliasChoices, ConfigDict, Field

from inference.core.entities.requests.paligemma import PaliGemmaInferenceRequest
from inference.core.managers.base import ModelManager
from inference.core.workflows.core_steps.common.utils import load_core_model
from inference.core.workflows.entities.base import OutputDefinition
from inference.core.workflows.entities.types import (
    BATCH_OF_PARENT_ID_KIND,
    BATCH_OF_STRING_KIND,
    STRING_KIND,
    FlowControl,
    StepOutputImageSelector,
    WorkflowImageSelector,
    WorkflowParameterSelector,
)
from inference.core.workflows.prototypes.block import (
    WorkflowBlock,
    WorkflowBlockManifest,
)

LONG_DESCRIPTION = """
PaliGemmaModel block is used to run PaliGemma model. It takes an image and a prompt as input and returns the model output.
"""


class BlockManifest(WorkflowBlockManifest):
    model_config = ConfigDict(
        json_schema_extra={
            "short_description": "Run PaliGemma model.",
            "long_description": LONG_DESCRIPTION,
            "license": "Apache-2.0",
            "block_type": "model",
        }
    )
    type: Literal["PaliGemmaModel"]
    images: Union[WorkflowImageSelector, StepOutputImageSelector] = Field(
        description="Reference at image to be used as input for step processing",
        examples=["$inputs.image", "$steps.cropping.crops"],
        validation_alias=AliasChoices("images", "image"),
    )
    prompt: Union[WorkflowParameterSelector(kind=[STRING_KIND]), str] = Field(
        description="Holds unconstrained text prompt to LMM mode",
        examples=["my prompt", "$inputs.prompt"],
    )

    @classmethod
    def describe_outputs(cls) -> List[OutputDefinition]:
        return [
            OutputDefinition(name="parent_id", kind=[BATCH_OF_PARENT_ID_KIND]),
            OutputDefinition(name="model_output", kind=[BATCH_OF_STRING_KIND]),
        ]


class PaliGemmaModelBlock(WorkflowBlock):

    def __init__(
        self,
        model_manager: ModelManager,
        api_key: Optional[str],
    ):
        self._model_manager = model_manager
        self._api_key = api_key

    @classmethod
    def get_init_parameters(cls) -> List[str]:
        return ["model_manager", "api_key"]

    @classmethod
    def get_manifest(cls) -> Type[WorkflowBlockManifest]:
        return BlockManifest

    async def run_locally(
        self,
        images: List[dict],
        prompt: str,
    ) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], FlowControl]]:

        responses = []

        for img in images:

            inference_request = PaliGemmaInferenceRequest(
                image=img, prompt=prompt, api_key=self._api_key
            )
            paligemma_model_id = load_core_model(
                model_manager=self._model_manager,
                inference_request=inference_request,
                core_model="paligemma",
            )

            response = await self._model_manager.infer_from_request(
                paligemma_model_id, inference_request
            )

            responses.append(
                {
                    "parent_id": img["parent_id"],
                    "model_output": response.response,
                }
            )

        return responses