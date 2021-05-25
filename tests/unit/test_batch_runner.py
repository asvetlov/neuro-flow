import pathlib
import pytest
import sys
from neuro_sdk import Client
from tempfile import TemporaryDirectory
from typing import AsyncContextManager, AsyncIterator, Callable, Iterator, Mapping

from neuro_flow.batch_runner import (
    build_graphs,
    check_image_refs_unique,
    check_local_deps,
    check_no_cycles,
    iter_flows,
    upload_image_data,
)
from neuro_flow.colored_topo_sorter import CycleError
from neuro_flow.config_loader import BatchLocalCL, ConfigLoader
from neuro_flow.context import EarlyBatchAction, RunningBatchFlow
from neuro_flow.parser import ConfigDir
from neuro_flow.storage import BakeImage, LocalFS, Storage
from tests.unit.test_batch_exector import MockStorage


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager
else:
    from async_generator import asynccontextmanager

BatchClFactory = Callable[[str], AsyncContextManager[ConfigLoader]]


@pytest.fixture
async def batch_cl_factory(
    loop: None,
    assets: pathlib.Path,
    client: Client,
) -> Callable[[str], AsyncContextManager[ConfigLoader]]:
    @asynccontextmanager
    async def _factory(subpath: str = "") -> AsyncIterator[ConfigLoader]:
        config_dir = ConfigDir(
            workspace=assets / subpath,
            config_dir=assets / subpath,
        )
        cl = BatchLocalCL(config_dir, client)
        yield cl
        await cl.close()

    return _factory


@pytest.fixture()
def batch_storage(loop: None) -> Iterator[Storage]:
    with TemporaryDirectory() as tmpdir:
        fs = LocalFS(pathlib.Path(tmpdir))
        yield MockStorage(fs)


async def test_iter_flows(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("early_graph") as cl:
        flow = await RunningBatchFlow.create(cl, "batch", "bake-id")
        prefix2flow = {prefix: flow async for prefix, flow in iter_flows(flow)}

        assert prefix2flow[()] == flow
        action_flow = prefix2flow[("second",)]
        assert isinstance(action_flow, EarlyBatchAction)
        assert action_flow._action == (await flow.get_action_early("second"))._action

        action_flow = prefix2flow[("third",)]
        assert isinstance(action_flow, EarlyBatchAction)
        assert action_flow._action == (await flow.get_action_early("third"))._action


async def test_check_no_cycles(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("") as cl:
        flow = await RunningBatchFlow.create(cl, "batch-cycle", "bake-id")
        with pytest.raises(CycleError):
            await check_no_cycles(flow)


async def test_check_cycles(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("") as cl:
        flow = await RunningBatchFlow.create(cl, "batch-cycle", "bake-id")
        with pytest.raises(CycleError):
            await check_no_cycles(flow)


async def test_local_deps_on_remote_1(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("local_actions") as cl:
        flow = await RunningBatchFlow.create(cl, "bad-order", "bake-id")
        with pytest.raises(
            Exception, match=r"Local action 'local' depends on remote task 'remote'"
        ):
            await check_local_deps(flow)


async def test_local_deps_on_remote_2(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("local_actions") as cl:
        flow = await RunningBatchFlow.create(cl, "bad-order-through-action", "bake-id")
        with pytest.raises(
            Exception,
            match=r"Local action 'local' depends on "
            r"remote task 'call_action.remote_task'",
        ):
            await check_local_deps(flow)


async def test_graphs(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("") as cl:
        flow = await RunningBatchFlow.create(cl, "batch-action-call", "bake-id")
        graphs = await build_graphs(flow)
        assert graphs == {
            (): {("test",): set()},
            ("test",): {
                ("test", "task_1"): set(),
                ("test", "task_2"): {("test", "task_1")},
            },
        }


async def test_early_graph(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("early_graph") as cl:
        flow = await RunningBatchFlow.create(cl, "batch", "bake-id")
        graphs = await build_graphs(flow)
        assert graphs == {
            (): {
                ("first_ac",): set(),
                ("second",): {("first_ac",)},
                ("third",): {("first_ac",)},
            },
            ("first_ac",): {("first_ac", "task_2"): set()},
            ("second",): {
                ("second", "task-1-o3-t3"): set(),
                ("second", "task-1-o1-t1"): set(),
                ("second", "task-1-o2-t1"): set(),
                ("second", "task-1-o2-t2"): set(),
                ("second", "task_2"): {
                    ("second", "task-1-o3-t3"),
                    ("second", "task-1-o1-t1"),
                    ("second", "task-1-o2-t1"),
                    ("second", "task-1-o2-t2"),
                },
            },
            ("third",): {
                ("third", "task-1-o3-t3"): set(),
                ("third", "task-1-o1-t1"): set(),
                ("third", "task-1-o2-t1"): set(),
                ("third", "task-1-o2-t2"): set(),
                ("third", "task_2"): {
                    ("third", "task-1-o3-t3"),
                    ("third", "task-1-o1-t1"),
                    ("third", "task-1-o2-t1"),
                    ("third", "task-1-o2-t2"),
                },
            },
        }


async def test_check_image_refs_unique(batch_cl_factory: BatchClFactory) -> None:
    async with batch_cl_factory("batch_images") as cl:
        flow = await RunningBatchFlow.create(cl, "duplicate_ref", "bake-id")
        with pytest.raises(
            Exception,
            match=r"Image ref 'image:banana1' is duplicated",
        ):
            await check_image_refs_unique(flow)


async def test_upload_image_data(
    batch_cl_factory: BatchClFactory,
    batch_storage: Storage,
    assets: pathlib.Path,
) -> None:
    async with batch_cl_factory("batch_images") as cl:
        flow = await RunningBatchFlow.create(cl, "batch", "bake-id")
        bake = await batch_storage.create_bake(
            "test",
            "batch",
            configs_meta={},
            configs=[],
            graphs={},
            params=None,
            name=None,
            tags=[],
        )

        runs = []

        async def _fake_run_cli(*args: str) -> None:
            runs.append(args)

        await upload_image_data(flow, bake, _fake_run_cli, batch_storage)

        ref2img: Mapping[str, BakeImage] = {
            image.ref: image async for image in batch_storage.list_bake_images(bake)
        }
        assert ref2img.keys() == {"image:main", "image:banana1", "image:banana2"}
        for ref in {"image:main", "image:banana1"}:
            img = ref2img[ref]
            assert img.context_on_storage
            assert img.dockerfile_rel == "Dockerfile"
            assert any(
                run == ("mkdir", "--parents", str(img.context_on_storage))
                for run in runs
            )
            assert any(
                run
                == (
                    "cp",
                    "--recursive",
                    "--update",
                    "--no-target-directory",
                    str(assets / "batch_images/dir"),
                    str(img.context_on_storage),
                )
                for run in runs
            )