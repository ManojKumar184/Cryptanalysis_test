"""Minimal read-only HTTP dashboard entry point for Docker Spaces."""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server

from learning.database import ExperienceDatabase
from monitoring.dashboard import html, snapshot
from worker import persistent_root


def application(environ, start_response):
    database = ExperienceDatabase(persistent_root() / "database" / "cryptoanalysis.sqlite")
    try:
        body = html(snapshot(database)).encode("utf-8")
    finally:
        database.close()
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    make_server("0.0.0.0", port, application).serve_forever()
