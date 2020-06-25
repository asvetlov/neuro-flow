# YAML parser
#
# The parser converts YAML entities into ast data classes.
#
# Defaults are evaluated by the separate processing step.


import datetime
import re
from functools import partial
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Dict

import trafaret as t
import yaml
from neuromation.api import HTTPPort
from yarl import URL

from . import ast


def _is_identifier(value: str) -> str:
    value.isidentifier()
    return value


def _beautify(filename: str) -> str:
    return filename.replace("_", " ").replace("-", " ").capitalize()


Id = t.WithRepr(
    t.OnError(
        t.String & str.isidentifier,
        "value is not an identifier",
        code="is_not_identifier",
    ),
    "<ID>",
)
OptKey = partial(t.Key, optional=True)
URI = t.WithRepr(t.String() & URL, "<URI>")
LocalPath = t.WithRepr(t.String() & Path, "<LocalPath>")
RemotePath = t.WithRepr(t.String() & PurePosixPath, "<RemotePath>")


def make_lifespan(match: "re.Match[str]") -> float:
    td = datetime.timedelta(
        days=int(match.group("d") or 0),
        hours=int(match.group("h") or 0),
        minutes=int(match.group("m") or 0),
        seconds=int(match.group("s") or 0),
    )
    return td.total_seconds()


RegexLifeSpan = (
    t.OnError(
        t.RegexpRaw(
            re.compile(r"^((?P<d>\d+)d)?((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s)?$")
        ),
        "value is not a lifespan, e.g. 1d2h3m4s",
    )
    & make_lifespan
)
LIFE_SPAN = t.WithRepr(t.Float | RegexLifeSpan, "<LifeSpan>")


VOLUME = t.Dict(
    {t.Key("uri"): URI, t.Key("mount"): RemotePath, t.Key("ro", default=False): t.Bool}
)


def parse_volume(id: str, data: Dict[str, Any]) -> ast.Volume:
    return ast.Volume(id=id, uri=data["uri"], mount=data["mount"], ro=data["ro"],)


IMAGE = t.Dict(
    {
        t.Key("uri"): URI,
        t.Key("context"): LocalPath,
        t.Key("dockerfile"): LocalPath,
        t.Key("build-args"): t.Mapping(t.String(), t.String()),
    }
)


def parse_image(id: str, data: Dict[str, Any]) -> ast.Image:
    return ast.Image(
        id=id,
        uri=data["uri"],
        context=data["context"],
        dockerfile=data["dockerfile"],
        build_args=MappingProxyType(data["build-args"]),
    )


EXEC_UNIT = t.Dict(
    {
        OptKey("name"): t.String,
        t.Key("image"): t.String,
        OptKey("preset"): t.String,
        OptKey("http"): t.Dict(
            {t.Key("port"): t.Int, t.Key("requires-auth", default=True): t.Bool}
        ),
        OptKey("entrypoint"): t.String,
        t.Key("cmd"): t.String,
        OptKey("workdir"): RemotePath,
        t.Key("env", default=dict): t.Mapping(t.String, t.String),
        t.Key("volumes", default=list): t.List(t.String),
        t.Key("tags", default=list): t.List(t.String),
        OptKey("life-span"): LIFE_SPAN,
    }
)


def parse_exec_unit(data: Dict[str, Any]) -> Dict[str, Any]:
    http = data.get("http")
    if http is not None:
        http = HTTPPort(http["port"], http["requires-auth"])
    return dict(
        name=data.get("name"),
        image=data["image"],
        preset=data.get("preset"),
        http=http,
        entrypoint=data.get("entrypoint"),
        cmd=data["cmd"],
        workdir=data.get("workdir"),
        env=data["env"],
        volumes=tuple(data["volumes"]),
        tags=frozenset(data["tags"]),
        life_span=data.get("life-span"),
    )


JOB = EXEC_UNIT.merge(
    t.Dict(
        {
            OptKey("title"): t.String,
            t.Key("detach", default=False): t.Bool,
            t.Key("browse", default=False): t.Bool,
        }
    )
)


def parse_job(id: str, data: Dict[str, Any]) -> ast.Job:
    return ast.Job(
        id=id,
        title=data.get("title"),
        detach=data["detach"],
        browse=data["browse"],
        **parse_exec_unit(data),
    )


BASE_FLOW = t.Dict(
    {
        t.Key("kind"): t.String,
        OptKey("title"): t.String,
        t.Key("images", default=dict): t.Mapping(t.String, IMAGE),
        t.Key("volumes", default=dict): t.Mapping(t.String, VOLUME),
        t.Key("tags", default=list): t.List(t.String),
        t.Key("env", default=dict): t.Mapping(t.String, t.String),
        OptKey("workdir"): RemotePath,
        OptKey("life-span"): LIFE_SPAN,
    }
)


def parse_base_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    return dict(
        kind=ast.Kind(data["kind"]),
        title=data.get("title"),
        images=MappingProxyType(
            {id: parse_image(id, image) for id, image in data["images"].items()}
        ),
        volumes=MappingProxyType(
            {id: parse_volume(id, volume) for id, volume in data["volumes"].items()}
        ),
        tags=frozenset(data["tags"]),
        env=MappingProxyType(data["env"]),
        workdir=data.get("workdir"),
        life_span=data.get("life-span"),
    )


INTERACTIVE_FLOW = BASE_FLOW.merge(t.Dict({t.Key("jobs"): t.Mapping(t.String, JOB)}))


def parse_interactive(data: Dict[str, Any]) -> ast.InteractiveFlow:
    data = INTERACTIVE_FLOW(data)
    assert data["kind"] == ast.Kind.JOB.value
    jobs = {id: parse_job(id, job) for id, job in data["jobs"].items()}
    return ast.InteractiveFlow(jobs=jobs, **parse_base_flow(data))


def parse(path: Path) -> ast.BaseFlow:
    with path.open() as f:
        data = yaml.safe_load(f)
    kind = data.get("kind")
    if kind is None:
        raise RuntimeError("Missing field 'kind'")
    elif kind == ast.Kind.JOB.value:
        return parse_interactive(data)
    else:
        raise RuntimeError(
            f"Unknown 'kind': {kind}, supported values are 'job' and 'batch'"
        )
