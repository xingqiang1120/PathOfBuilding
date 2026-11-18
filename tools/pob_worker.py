"""Client for the persistent Path of Building worker (tools/PobWorker.lua).

    from pob_worker import WORKER, WorkerError
    WORKER.call("metrics", {"xml": xml_text, "name": "My build"})

The worker loads Path of Building once (~4 s) and then answers requests over stdin/stdout.
"""
import json
import os
import subprocess
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WorkerError(Exception):
    """An error reported by Path of Building for a request (bad gem name, unknown slot, ...)."""


class Worker:
    def __init__(self):
        self.proc = None
        self.lock = threading.Lock()
        self.next_id = 0

    def start(self):
        cmd = [sys.executable, os.path.join(ROOT, "tools", "runlua.py"), os.path.join(ROOT, "tools", "PobWorker.lua")]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        for line in self.proc.stdout:
            if line.startswith("@@READY"):
                return
            if line.startswith("LUA ERROR"):
                break
        self.proc = None
        raise RuntimeError("Path of Building worker failed to start")

    def call(self, method, params):
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                self.start()
            self.next_id += 1
            self.proc.stdin.write(json.dumps({"id": self.next_id, "method": method, "params": params}) + "\n")
            self.proc.stdin.flush()
            for line in self.proc.stdout:
                if line.startswith("@@RESP "):
                    answer = json.loads(line[7:])
                    if not answer.get("ok"):
                        raise WorkerError(answer.get("error", "unknown error"))
                    return answer.get("result")
            self.proc = None
            raise RuntimeError("Path of Building worker stopped unexpectedly")

    def close(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.stdin.close()
            self.proc.wait(timeout=30)
        self.proc = None


WORKER = Worker()
