from pprint import pprint
from typing import List, Union

import json
import lm_eval.base

from . import flare
# Clear GPU memory
import torch
torch.cuda.empty_cache()
TASK_REGISTRY = {
    "flare_thEx": flare.ThExTask,
    "flare_idfinsent": flare.IDfinsent,
    "flare_IdFinReviewsSent": flare.IDFinReviewsSent,
    "flare_CCFraud": flare.CCFraudTask,
    "flare_craccf": flare.craccfTask,
    "flare_fbp": flare.FpbTask,
    "flare_Australian": flare.AustralianTask,
    "flare_sm_cikmID": flare.StockMovementCIKMID,
    "flare_vi_bigdata": flare.StockMovementBigDataVI,
    "flare_sm_aclPH": flare.StockMovementACLPH,
    "flare_sm_aclMY": flare.StockMovementACLMY,
    "flare_stockATh": flare.StockMovementStockA,
    "flare_fiqasa": flare.FIQASA,
    "flare_cra_lendingclub": flare.lendingclub,
    "flare_IDFinURLSum": flare.IDFinURLSumTask,
    "flare_VieRen": flare.VieComputerPartTask,
    "flare_MayRen": flare.MayComputerPartTask,
    "flare_ThaRen": flare.THComputerPartTask,
    "flare_IndRen": flare.IndComputerPartTask,
    "flare_FilRen": flare.FilComputerPartTask,

    **flare.SM_TASKS,
}


ALL_TASKS = sorted(list(TASK_REGISTRY))

_EXAMPLE_JSON_PATH = "split:key:/absolute/path/to/data.json"


def add_json_task(task_name):
    """Add a JSON perplexity task if the given task name matches the
    JSON task specification.

    See `json.JsonPerplexity`.
    """
    if not task_name.startswith("json"):
        return

    def create_json_task():
        splits = task_name.split("=", 1)
        if len(splits) != 2 or not splits[1]:
            raise ValueError(
                "json tasks need a path argument pointing to the local "
                "dataset, specified like this: json="
                + _EXAMPLE_JSON_PATH
                + ' (if there are no splits, use "train")'
            )

        json_path = splits[1]
        if json_path == _EXAMPLE_JSON_PATH:
            raise ValueError(
                "please do not copy the example path directly, but substitute "
                "it with a path to your local dataset"
            )
        return lambda: json.JsonPerplexity(json_path)

    TASK_REGISTRY[task_name] = create_json_task()


def get_task(task_name):
    try:
        add_json_task(task_name)
        return TASK_REGISTRY[task_name]
    except KeyError:
        print("Available tasks:")
        pprint(TASK_REGISTRY)
        raise KeyError(f"Missing task {task_name}")


def get_task_name_from_object(task_object):
    for name, class_ in TASK_REGISTRY.items():
        if class_ is task_object:
            return name

    # this gives a mechanism for non-registered tasks to have a custom name anyways when reporting
    return (
        task_object.EVAL_HARNESS_NAME
        if hasattr(task_object, "EVAL_HARNESS_NAME")
        else type(task_object).__name__
    )


def get_task_dict(task_name_list: List[Union[str, lm_eval.base.Task]]):
    task_name_dict = {
        task_name: get_task(task_name)()
        for task_name in task_name_list
        if isinstance(task_name, str)
    }
    task_name_from_object_dict = {
        get_task_name_from_object(task_object): task_object
        for task_object in task_name_list
        if not isinstance(task_object, str)
    }
    assert set(task_name_dict.keys()).isdisjoint(set(task_name_from_object_dict.keys()))
    return {**task_name_dict, **task_name_from_object_dict}
