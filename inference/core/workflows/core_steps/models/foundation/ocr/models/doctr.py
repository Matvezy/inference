from inference.core.entities.requests.doctr import DoctrOCRInferenceRequest
from inference.core.workflows.core_steps.common.entities import (
    StepExecutionMode,
)
from inference.core.workflows.core_steps.common.utils import load_core_model
from inference.core.workflows.execution_engine.entities.base import (
    Batch,
    WorkflowImageData,
)
from inference.core.workflows.prototypes.block import BlockResult
from typing import Callable, List

from .base import BaseOCRModel


class DoctrOCRModel(BaseOCRModel):

    def run(
        self,
        images: Batch[WorkflowImageData],
        step_execution_mode: StepExecutionMode,
        post_process_result: Callable[
            [Batch[WorkflowImageData], List[dict]], BlockResult
        ],
    ) -> BlockResult:
        if step_execution_mode is StepExecutionMode.LOCAL:
            return self.run_locally(images, post_process_result)
        elif step_execution_mode is StepExecutionMode.REMOTE:
            return self.run_remotely(images, post_process_result)

    def run_locally(
        self,
        images: Batch[WorkflowImageData],
        post_process_result: Callable[
            [Batch[WorkflowImageData], List[dict]], BlockResult
        ],
    ) -> BlockResult:
        predictions = []
        for single_image in images:
            inference_request = DoctrOCRInferenceRequest(
                image=single_image.to_inference_format(numpy_preferred=True),
                api_key=self.api_key,
            )
            doctr_model_id = load_core_model(
                model_manager=self.model_manager,
                inference_request=inference_request,
                core_model="doctr",
            )
            result = self.model_manager.infer_from_request_sync(
                doctr_model_id, inference_request
            )
            predictions.append(result.model_dump())
        return post_process_result(images, predictions)

    def run_remotely(
        self,
        images: Batch[WorkflowImageData],
        post_process_result: Callable[
            [Batch[WorkflowImageData], List[dict]], BlockResult
        ],
    ) -> BlockResult:
        raise NotImplementedError(
            "Remote execution is not implemented for DoctrOCRModel."
        )
