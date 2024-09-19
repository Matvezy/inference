import numpy as np
import pytest
import supervision as sv

from inference.core.env import WORKFLOWS_MAX_CONCURRENT_STEPS
from inference.core.managers.base import ModelManager
from inference.core.workflows.core_steps.common.entities import StepExecutionMode
from inference.core.workflows.core_steps.common.query_language.errors import (
    EvaluationEngineError,
)
from inference.core.workflows.errors import RuntimeInputError, StepExecutionError
from inference.core.workflows.execution_engine.core import ExecutionEngine
from tests.workflows.integration_tests.execution.workflows_gallery_collector.decorators import (
    add_to_workflows_gallery,
)

TOP_PREDICTION_WORKFLOW = {
    "version": "1.0",
    "inputs": [
        {"type": "WorkflowImage", "name": "image"},
        {"type": "WorkflowParameter", "name": "model_id"},
        {"type": "WorkflowParameter", "name": "confidence", "default_value": 0.3},
        {"type": "WorkflowParameter", "name": "classes"},
    ],
    "steps": [
        {
            "type": "ObjectDetectionModel",
            "name": "model",
            "image": "$inputs.image",
            "model_id": "$inputs.model_id",
            "confidence": "$inputs.confidence",
        },
        {
            "type": "DetectionsTransformation",
            "name": "take_top_prediction",
            "predictions": "$steps.model.predictions",
            "operations": [{"type": "DetectionsSelection", "mode": "top_confidence"}],
        },
    ],
    "outputs": [
        {
            "type": "JsonField",
            "name": "all_predictions",
            "selector": "$steps.model.predictions",
        },
        {
            "type": "JsonField",
            "name": "top_prediction",
            "selector": "$steps.take_top_prediction.predictions",
        },
    ],
}

EXPECTED_OBJECT_DETECTION_BBOXES = np.array(
    [
        [180, 273, 244, 383],
        [271, 266, 328, 383],
        [552, 259, 598, 365],
        [113, 269, 145, 347],
        [416, 258, 457, 365],
        [521, 257, 555, 360],
        [387, 264, 414, 342],
        [158, 267, 183, 349],
        [324, 256, 345, 320],
        [341, 261, 362, 338],
        [247, 251, 262, 284],
        [239, 251, 249, 282],
    ]
)
EXPECTED_OBJECT_DETECTION_CONFIDENCES = np.array(
    [
        0.84284,
        0.83957,
        0.81555,
        0.80455,
        0.75804,
        0.75794,
        0.71715,
        0.71408,
        0.71003,
        0.56938,
        0.54092,
        0.43511,
    ]
)


def test_filtering_workflow_to_include_only_top_prediction(
    model_manager: ModelManager,
    crowd_image: np.ndarray,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
        "workflows_core.step_execution_mode": StepExecutionMode.LOCAL,
    }
    execution_engine = ExecutionEngine.init(
        workflow_definition=TOP_PREDICTION_WORKFLOW,
        init_parameters=workflow_init_parameters,
        max_concurrent_steps=WORKFLOWS_MAX_CONCURRENT_STEPS,
    )

    # when
    result = execution_engine.run(
        runtime_parameters={
            "image": crowd_image,
            "model_id": "yolov8n-640",
            "classes": {"person"},
        }
    )

    # then
    assert isinstance(result, list), "Expected result to be list"
    assert len(result) == 1, "Single image provided - single output expected"
    all_detections: sv.Detections = result[0]["all_predictions"]
    top_detections: sv.Detections = result[0]["top_prediction"]

    assert len(all_detections) == 12, "Expected 12 total predictions"
    assert np.allclose(
        all_detections.xyxy,
        EXPECTED_OBJECT_DETECTION_BBOXES,
        atol=1,
    ), "Expected bboxes to match what was validated manually as workflow outcome"
    assert np.allclose(
        all_detections.confidence,
        EXPECTED_OBJECT_DETECTION_CONFIDENCES,
        atol=0.01,
    ), "Expected confidences to match what was validated manually as workflow outcome"

    assert len(top_detections) == 1, "Expected only one top prediction"
    assert np.allclose(
        top_detections.xyxy,
        [EXPECTED_OBJECT_DETECTION_BBOXES[0]],
        atol=1,
    ), "Expected top bbox to match what was validated manually as workflow outcome"
    assert np.allclose(
        top_detections.confidence,
        [EXPECTED_OBJECT_DETECTION_CONFIDENCES[0]],
        atol=0.01,
    ), "Expected top confidence to match what was validated manually as workflow outcome"


def test_filtering_workflow_by_top_prediction_with_no_detections(
    model_manager: ModelManager,
    red_image: np.ndarray,
) -> None:
    # given
    workflow_init_parameters = {
        "workflows_core.model_manager": model_manager,
        "workflows_core.api_key": None,
        "workflows_core.step_execution_mode": StepExecutionMode.LOCAL,
    }
    execution_engine = ExecutionEngine.init(
        workflow_definition=TOP_PREDICTION_WORKFLOW,
        init_parameters=workflow_init_parameters,
        max_concurrent_steps=WORKFLOWS_MAX_CONCURRENT_STEPS,
    )

    # when
    result = execution_engine.run(
        runtime_parameters={
            "image": red_image,
            "model_id": "yolov8n-640",
            "classes": {"not_present"},
        }
    )

    # then
    assert isinstance(result, list), "Expected result to be list"
    assert len(result) == 1, "Single image provided - single output expected"
    all_detections: sv.Detections = result[0]["all_predictions"]
    top_detections: sv.Detections = result[0]["top_prediction"]

    assert len(all_detections) == 0, "Expected 0 total predictions"
    assert len(top_detections) == 0, "Expected top prediction to be an empty array"
