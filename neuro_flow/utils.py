import click
from neuromation.api import JobStatus


COLORS = {
    JobStatus.PENDING: "yellow",
    JobStatus.RUNNING: "blue",
    JobStatus.SUCCEEDED: "green",
    JobStatus.FAILED: "red",
    JobStatus.UNKNOWN: "yellow",
}


def format_job_status(status: JobStatus) -> str:
    return click.style(status.value, fg=COLORS.get(status, "reset"))