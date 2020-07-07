# YAML parser
#
# The parser converts YAML entities into ast data classes.
#
# Defaults are evaluated by the separate processing step.


import datetime
import re
from functools import partial
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional, Union

import trafaret as t
import yaml
from yarl import URL

from . import ast
from .expr import (
    BoolExpr,
    LocalPathExpr,
    OptBoolExpr,
    OptFloatExpr,
    OptIntExpr,
    OptRemotePathExpr,
    OptStrExpr,
    RemotePathExpr,
    StrExpr,
    URIExpr,
)
from .types import RemotePath as RemotePathType


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
EXPR_RE = re.compile(r"\$\{\{.+\}\}")
OptKey = partial(t.Key, optional=True)
Expr = t.WithRepr(t.Regexp(EXPR_RE), "<Expr>")
URI = t.WithRepr(t.String & URL & str | Expr, "<URI>")


LocalPath = t.WithRepr((t.String() & Path & str) | Expr, "<LocalPath>")
RemotePath = t.WithRepr((t.String() & PurePosixPath & str) | Expr, "<RemotePath>")


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
LIFE_SPAN = t.WithRepr(t.Float & str | RegexLifeSpan & str, "<LifeSpan>")


VOLUME = t.Dict(
    {
        t.Key("uri"): URI,
        t.Key("mount"): RemotePath,
        t.Key("ro", default=False): (t.Bool & str | Expr),
    }
)


def parse_volume(id: str, data: Dict[str, Any]) -> ast.Volume:
    return ast.Volume(
        id=id,
        uri=URIExpr(data["uri"]),
        mount=RemotePathExpr(data["mount"]),
        ro=BoolExpr(data["ro"]),
    )


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
        uri=URIExpr(data["uri"]),
        context=LocalPathExpr(data["context"]),
        dockerfile=LocalPathExpr(data["dockerfile"]),
        build_args={str(k): StrExpr(v) for k, v in data["build-args"].items()},
    )


EXEC_UNIT = t.Dict(
    {
        OptKey("title"): t.String,
        OptKey("name"): t.String,
        t.Key("image"): t.String,
        OptKey("preset"): t.String,
        OptKey("entrypoint"): t.String,
        t.Key("cmd"): t.String,
        OptKey("workdir"): RemotePath,
        t.Key("env", default=dict): t.Mapping(t.String, t.String),
        t.Key("volumes", default=list): t.List(t.String),
        t.Key("tags", default=list): t.List(t.String),
        OptKey("life-span"): LIFE_SPAN | Expr,
        OptKey("http-port"): t.Int & str | Expr,
        OptKey("http-auth"): t.Bool & str | Expr,
    }
)


def parse_exec_unit(id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return dict(
        id=id,
        title=OptStrExpr(data.get("title")),
        name=OptStrExpr(data.get("name")),
        image=StrExpr(data["image"]),
        preset=OptStrExpr(data.get("preset")),
        entrypoint=OptStrExpr(data.get("entrypoint")),
        cmd=StrExpr(data["cmd"]),
        workdir=OptRemotePathExpr(data.get("workdir")),
        env={str(k): StrExpr(v) for k, v in data["env"].items()},
        volumes=[StrExpr(v) for v in data["volumes"]],
        tags={StrExpr(t) for t in data["tags"]},
        life_span=OptFloatExpr(data.get("life-span")),
        http_port=OptIntExpr(data.get("http-port")),
        http_auth=OptBoolExpr(data.get("http-auth")),
    )


JOB = EXEC_UNIT.merge(
    t.Dict(
        {
            t.Key("detach", default=False): t.Bool & str,
            t.Key("browse", default=False): t.Bool & str,
        }
    )
)


def parse_job(id: str, data: Dict[str, Any]) -> ast.Job:
    return ast.Job(
        detach=BoolExpr(data["detach"]),
        browse=BoolExpr(data["browse"]),
        **parse_exec_unit(id, data),
    )


FLOW_DEFAULTS = t.Dict(
    {
        t.Key("tags", default=list): t.List(t.String),
        t.Key("env", default=dict): t.Mapping(t.String, t.String),
        OptKey("workdir"): RemotePath,
        OptKey("life-span"): LIFE_SPAN,
    }
)


BASE_FLOW = t.Dict(
    {
        t.Key("kind"): t.String,
        OptKey("id"): t.String,
        OptKey("title"): t.String,
        t.Key("images", default=dict): t.Mapping(t.String, IMAGE),
        t.Key("volumes", default=dict): t.Mapping(t.String, VOLUME),
        OptKey("defaults"): FLOW_DEFAULTS,
    }
)


def parse_flow_defaults(data: Optional[Dict[str, Any]]) -> ast.FlowDefaults:
    if data is None:
        return ast.FlowDefaults()
    workdir = data.get("workdir")
    life_span = data.get("life-span")
    return ast.FlowDefaults(
        tags={str(t) for t in data["tags"]},
        env={str(k): str(v) for k, v in data["env"].items()},
        workdir=RemotePathType(workdir) if workdir is not None else None,
        life_span=float(life_span) if life_span is not None else None,
    )


def parse_base_flow(default_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return dict(
        id=str(data.get("id", default_id)),
        kind=ast.Kind(data["kind"]),
        title=OptStrExpr(data.get("title")),
        images={
            str(id): parse_image(str(id), image) for id, image in data["images"].items()
        },
        volumes={
            str(id): parse_volume(str(id), volume)
            for id, volume in data["volumes"].items()
        },
        defaults=parse_flow_defaults(data.get("defaults")),
    )


INTERACTIVE_FLOW = BASE_FLOW.merge(t.Dict({t.Key("jobs"): t.Mapping(t.String, JOB)}))


def _parse_interactive(default_id: str, data: Dict[str, Any]) -> ast.InteractiveFlow:
    data = INTERACTIVE_FLOW(data)
    assert data["kind"] == ast.Kind.JOB.value
    jobs = {str(id): parse_job(str(id), job) for id, job in data["jobs"].items()}
    return ast.InteractiveFlow(jobs=jobs, **parse_base_flow(default_id, data))


def _calc_interactive_default_id(path: Path) -> str:
    if path.parts[-2:] == (".neuro", "jobs.yml"):
        default_id = path.parts[-3]
    else:
        default_id = path.stem
    return default_id


def parse_interactive(path: Path) -> ast.InteractiveFlow:
    # Parse interactive flow config file
    with path.open() as f:
        data = yaml.safe_load(f)
        return _parse_interactive(_calc_interactive_default_id(path), data)


def parse(path: Path) -> ast.BaseFlow:
    # Parse flow config file
    with path.open() as f:
        data = yaml.safe_load(f)
    kind = data.get("kind")
    if kind is None:
        raise RuntimeError("Missing field 'kind'")
    elif kind == ast.Kind.JOB.value:
        return _parse_interactive(_calc_interactive_default_id(path), data)
    else:
        raise RuntimeError(
            f"Unknown 'kind': {kind}, supported values are 'job' and 'batch'"
        )


def find_interactive_config(path: Optional[Union[Path, str]]) -> Path:
    # Find interactive config file, starting from path.
    #
    # If path is a file -- it is used as is.
    # If path is a directory -- it is used as starting point, Path.cwd() otherwise.
    # The lookup searches bottom-top from path dir up to the root folder,
    # looking for .neuro folder and ./neuro/jobs.yml
    # If the config file not found -- raise an exception.

    if path is not None:
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            raise ValueError(f"{path} does not exist")
        if path.is_file():
            return path
        if not path.is_dir():
            raise ValueError(f"{path} should be a file or directory")
    else:
        path = Path.cwd()

    orig_path = path

    while True:
        if path == path.parent:
            raise ValueError(f".neuro folder was not found in lookup for {orig_path}")
        if (path / ".neuro").is_dir():
            break
        path = path.parent

    ret = path / ".neuro" / "jobs.yml"
    if not ret.exists():
        raise ValueError(f"{ret} does not exist")
    if not ret.is_file():
        raise ValueError(f"{ret} is not a file")
    return ret
