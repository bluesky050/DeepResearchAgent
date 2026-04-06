"""Security Scan Tool - Run bandit for security vulnerability detection."""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import Field, ConfigDict

from src.tool.types import Tool, ToolResponse, ToolExtra
from src.registry import TOOL
from src.logger import logger


_SECURITY_SCAN_DESCRIPTION = """Security vulnerability scanner using bandit.

Scans Python code for common security issues including:
- SQL injection vulnerabilities
- Hardcoded passwords and secrets
- Use of insecure functions (eval, exec, pickle)
- Weak cryptography
- Shell injection risks
- Path traversal vulnerabilities

Args:
- code_path (str): Absolute path to Python file or directory to scan
- severity_level (Optional[str]): Minimum severity to report - "low", "medium", "high" (default: "low")
- confidence_level (Optional[str]): Minimum confidence to report - "low", "medium", "high" (default: "low")
- bandit_args (Optional[str]): Additional bandit arguments

Returns structured JSON with vulnerabilities categorized by risk level.

Example: {"name": "security_scan", "args": {"code_path": "/path/to/code.py", "severity_level": "medium"}}
"""

@TOOL.register_module(force=True)
class SecurityScanTool(Tool):
    """Security vulnerability scanner using bandit."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = "security_scan"
    description: str = _SECURITY_SCAN_DESCRIPTION
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=False)
    timeout: int = Field(default=120, description="Timeout in seconds")

    async def __call__(
        self,
        code_path: str,
        severity_level: Optional[str] = "low",
        confidence_level: Optional[str] = "low",
        bandit_args: Optional[str] = None,
        **kwargs
    ) -> ToolResponse:
        """Run security scan on Python code."""

        if not os.path.exists(code_path):
            return ToolResponse(
                success=False,
                message=f"Path does not exist: {code_path}"
            )

        # Validate severity and confidence levels
        valid_levels = ["low", "medium", "high"]
        if severity_level not in valid_levels:
            severity_level = "low"
        if confidence_level not in valid_levels:
            confidence_level = "low"

        # Run bandit
        result = await self._run_bandit(code_path, severity_level, confidence_level, bandit_args)

        if result is None:
            return ToolResponse(
                success=False,
                message="Failed to run bandit security scan"
            )

        # Categorize by risk level
        high_risk = [v for v in result["vulnerabilities"] if v["severity"] == "HIGH"]
        medium_risk = [v for v in result["vulnerabilities"] if v["severity"] == "MEDIUM"]
        low_risk = [v for v in result["vulnerabilities"] if v["severity"] == "LOW"]

        categorized = {
            "code_path": code_path,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "summary": result["summary"]
        }

        # Generate summary message
        total = len(result["vulnerabilities"])
        message = f"Security scan completed for {code_path}\n"
        message += f"Total vulnerabilities: {total}\n"
        message += f"  High risk: {len(high_risk)}\n"
        message += f"  Medium risk: {len(medium_risk)}\n"
        message += f"  Low risk: {len(low_risk)}\n"

        if high_risk:
            message += f"\nHigh risk vulnerabilities:\n"
            for vuln in high_risk[:5]:
                message += f"  [{vuln['test_id']}] {vuln['file']}:{vuln['line']} - {vuln['issue_text']}\n"

        if medium_risk and len(high_risk) < 5:
            message += f"\nMedium risk vulnerabilities:\n"
            for vuln in medium_risk[:5]:
                message += f"  [{vuln['test_id']}] {vuln['file']}:{vuln['line']} - {vuln['issue_text']}\n"

        return ToolResponse(
            success=True,
            message=message.strip(),
            extra=ToolExtra(data=categorized)
        )

    async def _run_bandit(
        self,
        code_path: str,
        severity_level: str,
        confidence_level: str,
        extra_args: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Run bandit and parse output."""
        try:
            # Build bandit command with JSON output
            severity_map = {"low": "l", "medium": "m", "high": "h"}
            confidence_map = {"low": "l", "medium": "m", "high": "h"}

            sev = severity_map.get(severity_level, "l")
            conf = confidence_map.get(confidence_level, "l")

            cmd = f"bandit -r -f json -ll -ii {extra_args or ''} \"{code_path}\""

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
                logger.warning(f"Bandit timed out after {self.timeout} seconds")
                return None

            stdout_str = stdout.decode('utf-8', errors='replace').strip()

            # Parse JSON output
            if stdout_str:
                try:
                    bandit_data = json.loads(stdout_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse bandit JSON output")
                    return None

                vulnerabilities = []
                for result in bandit_data.get("results", []):
                    # Filter by severity and confidence
                    sev_level = result.get("issue_severity", "LOW")
                    conf_level = result.get("issue_confidence", "LOW")

                    # Apply filters
                    if not self._meets_threshold(sev_level, severity_level):
                        continue
                    if not self._meets_threshold(conf_level, confidence_level):
                        continue

                    vulnerabilities.append({
                        "file": result.get("filename", ""),
                        "line": result.get("line_number", 0),
                        "severity": sev_level,
                        "confidence": conf_level,
                        "issue_text": result.get("issue_text", ""),
                        "test_id": result.get("test_id", ""),
                        "test_name": result.get("test_name", ""),
                        "code": result.get("code", ""),
                        "more_info": result.get("more_info", "")
                    })

                # Get metrics
                metrics = bandit_data.get("metrics", {})
                total_loc = sum([m.get("loc", 0) for m in metrics.values() if isinstance(m, dict)])

                summary = {
                    "total_vulnerabilities": len(vulnerabilities),
                    "total_loc": total_loc,
                    "files_scanned": len(metrics) - 1 if "_totals" in metrics else len(metrics)
                }

                return {
                    "vulnerabilities": vulnerabilities,
                    "summary": summary
                }

            return {"vulnerabilities": [], "summary": {"total_vulnerabilities": 0, "total_loc": 0, "files_scanned": 0}}

        except Exception as e:
            logger.error(f"Error running bandit: {e}")
            return None

    def _meets_threshold(self, level: str, threshold: str) -> bool:
        """Check if level meets threshold."""
        level_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        threshold_map = {"low": 0, "medium": 1, "high": 2}

        level_val = level_map.get(level.upper(), 0)
        threshold_val = threshold_map.get(threshold.lower(), 0)

        return level_val >= threshold_val
