"""Static Analysis Tool - Run pylint and flake8 for code quality checks."""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import Field, ConfigDict

from src.tool.types import Tool, ToolResponse, ToolExtra
from src.registry import TOOL
from src.logger import logger


_STATIC_ANALYSIS_DESCRIPTION = """Static code analysis tool using pylint and flake8.

Analyzes Python code for quality issues including:
- Code style violations (PEP8)
- Code complexity and maintainability issues
- Naming conventions
- Unused imports and variables
- Potential bugs and errors

Args:
- code_path (str): Absolute path to Python file or directory to analyze
- tools (Optional[List[str]]): List of tools to run - ["pylint", "flake8"] (default: both)
- pylint_args (Optional[str]): Additional pylint arguments (e.g., "--disable=C0111")
- flake8_args (Optional[str]): Additional flake8 arguments (e.g., "--max-line-length=100")

Returns structured JSON with issues categorized by severity.

Example: {"name": "static_analysis", "args": {"code_path": "/path/to/code.py"}}
"""

@TOOL.register_module(force=True)
class StaticAnalysisTool(Tool):
    """Static code analysis tool using pylint and flake8."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = "static_analysis"
    description: str = _STATIC_ANALYSIS_DESCRIPTION
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=False)
    timeout: int = Field(default=120, description="Timeout in seconds")

    async def __call__(
        self,
        code_path: str,
        tools: Optional[List[str]] = None,
        pylint_args: Optional[str] = None,
        flake8_args: Optional[str] = None,
        **kwargs
    ) -> ToolResponse:
        """Run static analysis on Python code."""

        if not os.path.exists(code_path):
            return ToolResponse(
                success=False,
                message=f"Path does not exist: {code_path}"
            )

        if tools is None:
            tools = ["pylint", "flake8"]

        results = {
            "code_path": code_path,
            "issues": [],
            "summary": {}
        }

        # Run pylint
        if "pylint" in tools:
            pylint_result = await self._run_pylint(code_path, pylint_args)
            if pylint_result:
                results["issues"].extend(pylint_result["issues"])
                results["summary"]["pylint"] = pylint_result["summary"]

        # Run flake8
        if "flake8" in tools:
            flake8_result = await self._run_flake8(code_path, flake8_args)
            if flake8_result:
                results["issues"].extend(flake8_result["issues"])
                results["summary"]["flake8"] = flake8_result["summary"]

        # Sort issues by severity
        severity_order = {"error": 0, "warning": 1, "convention": 2, "refactor": 3, "info": 4}
        results["issues"].sort(key=lambda x: (severity_order.get(x["severity"], 5), x["file"], x["line"]))

        # Generate summary message
        total_issues = len(results["issues"])
        by_severity = {}
        for issue in results["issues"]:
            sev = issue["severity"]
            by_severity[sev] = by_severity.get(sev, 0) + 1

        message = f"Static analysis completed for {code_path}\n"
        message += f"Total issues: {total_issues}\n"
        if by_severity:
            message += "By severity: " + ", ".join([f"{k}: {v}" for k, v in sorted(by_severity.items())]) + "\n"

        if total_issues > 0:
            message += f"\nTop 10 issues:\n"
            for issue in results["issues"][:10]:
                message += f"  [{issue['severity']}] {issue['file']}:{issue['line']} - {issue['message']}\n"

        return ToolResponse(
            success=True,
            message=message.strip(),
            extra=ToolExtra(data=results)
        )

    async def _run_pylint(self, code_path: str, extra_args: Optional[str]) -> Optional[Dict[str, Any]]:
        """Run pylint and parse output."""
        try:
            # Build pylint command with JSON output
            cmd = f"pylint --output-format=json {extra_args or ''} \"{code_path}\""

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.warning(f"Pylint timed out after {self.timeout} seconds")
                return None

            stdout_str = stdout.decode('utf-8', errors='replace').strip()

            # Parse JSON output
            if stdout_str:
                try:
                    pylint_data = json.loads(stdout_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse pylint JSON output")
                    return None

                issues = []
                for item in pylint_data:
                    issues.append({
                        "tool": "pylint",
                        "file": item.get("path", ""),
                        "line": item.get("line", 0),
                        "column": item.get("column", 0),
                        "severity": item.get("type", "").lower(),
                        "message": item.get("message", ""),
                        "symbol": item.get("symbol", ""),
                        "message_id": item.get("message-id", "")
                    })

                return {
                    "issues": issues,
                    "summary": {
                        "total": len(issues),
                        "tool": "pylint"
                    }
                }

            return {"issues": [], "summary": {"total": 0, "tool": "pylint"}}

        except Exception as e:
            logger.error(f"Error running pylint: {e}")
            return None

    async def _run_flake8(self, code_path: str, extra_args: Optional[str]) -> Optional[Dict[str, Any]]:
        """Run flake8 and parse output."""
        try:
            # Build flake8 command with format for easy parsing
            cmd = f"flake8 --format='%(path)s:%(row)d:%(col)d: %(code)s %(text)s' {extra_args or ''} \"{code_path}\""

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.warning(f"Flake8 timed out after {self.timeout} seconds")
                return None

            stdout_str = stdout.decode('utf-8', errors='replace').strip()

            issues = []
            if stdout_str:
                for line in stdout_str.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # Parse format: path:line:col: code message
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        file_path = parts[0].strip()
                        line_num = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                        col_num = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                        rest = parts[3].strip()

                        # Extract code and message
                        code_parts = rest.split(' ', 1)
                        code = code_parts[0] if code_parts else ""
                        message = code_parts[1] if len(code_parts) > 1 else ""

                        # Map flake8 codes to severity
                        severity = "warning"
                        if code.startswith('E'):
                            severity = "error"
                        elif code.startswith('W'):
                            severity = "warning"
                        elif code.startswith('C'):
                            severity = "convention"

                        issues.append({
                            "tool": "flake8",
                            "file": file_path,
                            "line": line_num,
                            "column": col_num,
                            "severity": severity,
                            "message": message,
                            "code": code
                        })

            return {
                "issues": issues,
                "summary": {
                    "total": len(issues),
                    "tool": "flake8"
                }
            }

        except Exception as e:
            logger.error(f"Error running flake8: {e}")
            return None
