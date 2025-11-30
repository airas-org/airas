import asyncio
import time
from copy import deepcopy
from functools import wraps
from logging import getLogger
from typing import Callable

from typing_extensions import Annotated, TypedDict

logger = getLogger(__name__)


ExecutionTime = dict[str, list[float]]


def merge_execution_time(
    left: ExecutionTime | None, right: ExecutionTime | None
) -> ExecutionTime:
    merged = deepcopy(left) if left else {}
    if not right:
        return merged
    for node, durations in right.items():
        existing = merged.setdefault(node, [])
        existing_len = len(existing)
        new_len = len(durations)
        if new_len >= existing_len:
            existing.extend(durations[existing_len:])
        else:
            existing.clear()
            existing.extend(durations)
    return merged


class ExecutionTimeState(TypedDict, total=False):
    execution_time: Annotated[ExecutionTime, merge_execution_time]


def time_node(
    subgraph_name: str, node_name: str | None = None
) -> Callable[..., Callable[..., object]]:
    def decorator(func):
        actual_node = node_name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(self, state, *args, **kwargs):
                header = f"[{subgraph_name}.{actual_node}]".ljust(40)
                logger.info(f"{header} Start")
                start = time.time()

                result = await func(self, state, *args, **kwargs)
                end = time.time()
                duration = round(end - start, 4)

                execution_time = state.get("execution_time", {})
                existing = execution_time.get(actual_node, [])
                execution_time[actual_node] = [*existing, duration]
                result["execution_time"] = execution_time

                logger.info(f"{header} End    Execution Time: {duration:7.4f} seconds")
                return result

            wrapper = async_wrapper

        else:

            @wraps(func)
            def sync_wrapper(self, state, *args, **kwargs):
                header = f"[{subgraph_name}.{actual_node}]".ljust(40)
                logger.info(f"{header} Start")
                start = time.time()

                result = func(self, state, *args, **kwargs)
                end = time.time()
                duration = round(end - start, 4)

                execution_time = state.get("execution_time", {})
                existing = execution_time.get(actual_node, [])
                execution_time[actual_node] = [*existing, duration]
                result["execution_time"] = execution_time

                logger.info(f"{header} End    Execution Time: {duration:7.4f} seconds")
                return result

            wrapper = sync_wrapper

        return wrapper

    return decorator


def time_subgraph(subgraph_name: str):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(state, *args, **kwargs):
                header = f"[{subgraph_name}]".ljust(40)
                logger.info(f"{header} Start")
                start = time.time()
                result = await func(state, *args, **kwargs)
                end = time.time()
                duration = round(end - start, 4)

                timings = state.get("execution_time", {})
                key = f"__{subgraph_name}_total__"
                existing = timings.get(key, [])
                timings[key] = [*existing, duration]
                state["execution_time"] = timings

                logger.info(f"{header} End    Execution Time: {duration:7.4f} seconds")
                return result

            wrapper = async_wrapper

        else:

            @wraps(func)
            def sync_wrapper(state, *args, **kwargs):
                header = f"[{subgraph_name}]".ljust(40)
                logger.info(f"{header} Start")
                start = time.time()
                result = func(state, *args, **kwargs)
                end = time.time()
                duration = round(end - start, 4)

                timings = state.get("execution_time", {})
                key = f"__{subgraph_name}_total__"
                existing = timings.get(key, [])
                timings[key] = [*existing, duration]
                state["execution_time"] = timings

                logger.info(f"{header} End    Execution Time: {duration:7.4f} seconds")
                return result

            wrapper = sync_wrapper

        return wrapper

    return decorator


__all__ = ["time_node", "time_subgraph", "ExecutionTimeState"]
