from pydantic import BaseModel


class CodeExecuteRequest(BaseModel):
    code: str
    framework: str = "qiskit"


class CodeExecuteResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    result: dict | None = None
