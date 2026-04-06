"""GitHub PR Tool - Operations for GitHub Pull Requests."""

import os
import tempfile
import shutil
from typing import Optional, Dict, Any, List, Literal
from pydantic import Field, ConfigDict

from src.tool.types import Tool, ToolResponse, ToolExtra
from src.registry import TOOL
from src.logger import logger

try:
    from github import Github, GithubException
    from git import Repo
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    logger.warning("PyGithub or GitPython not installed. Install with: pip install PyGithub GitPython")


_GITHUB_PR_DESCRIPTION = """GitHub Pull Request operations tool.

Provides comprehensive PR operations including:
- get_pr_info: Fetch PR metadata (title, description, author, status, etc.)
- get_pr_files: List all files changed in the PR
- get_pr_diff: Get the complete diff of all changes
- clone_pr_branch: Clone the PR branch to local directory for analysis
- create_pr_review: Post a review comment to the PR

Args:
- action (str): Operation to perform - one of: get_pr_info, get_pr_files, get_pr_diff, clone_pr_branch, create_pr_review
- repo (str): Repository in format "owner/repo" (e.g., "facebook/react")
- pr_number (int): Pull request number
- token (Optional[str]): GitHub personal access token (defaults to GITHUB_TOKEN env var)
- clone_path (Optional[str]): Local path for clone_pr_branch action
- review_body (Optional[str]): Review comment body for create_pr_review action
- review_event (Optional[str]): Review event type - COMMENT, APPROVE, or REQUEST_CHANGES (default: COMMENT)

Example: {"name": "github_pr", "args": {"action": "get_pr_info", "repo": "owner/repo", "pr_number": 42}}
"""

@TOOL.register_module(force=True)
class GitHubPRTool(Tool):
    """GitHub Pull Request operations tool."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = "github_pr"
    description: str = _GITHUB_PR_DESCRIPTION
    metadata: Dict[str, Any] = Field(default_factory=dict)
    require_grad: bool = Field(default=False)

    async def __call__(
        self,
        action: Literal["get_pr_info", "get_pr_files", "get_pr_diff", "clone_pr_branch", "create_pr_review"],
        repo: str,
        pr_number: int,
        token: Optional[str] = None,
        clone_path: Optional[str] = None,
        review_body: Optional[str] = None,
        review_event: Optional[str] = "COMMENT",
        **kwargs
    ) -> ToolResponse:
        """Execute GitHub PR operation."""

        if not GITHUB_AVAILABLE:
            return ToolResponse(
                success=False,
                message="PyGithub or GitPython not installed. Install with: pip install PyGithub GitPython"
            )

        # Get token from env if not provided
        if token is None:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                return ToolResponse(
                    success=False,
                    message="GitHub token not provided. Set GITHUB_TOKEN environment variable or pass token parameter."
                )

        try:
            gh = Github(token)
            repository = gh.get_repo(repo)
            pr = repository.get_pull(pr_number)

            if action == "get_pr_info":
                return await self._get_pr_info(pr)
            elif action == "get_pr_files":
                return await self._get_pr_files(pr)
            elif action == "get_pr_diff":
                return await self._get_pr_diff(pr)
            elif action == "clone_pr_branch":
                return await self._clone_pr_branch(pr, repo, clone_path, token)
            elif action == "create_pr_review":
                return await self._create_pr_review(pr, review_body, review_event)
            else:
                return ToolResponse(
                    success=False,
                    message=f"Unknown action: {action}"
                )

        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            return ToolResponse(
                success=False,
                message=f"GitHub API error: {e.data.get('message', str(e))}"
            )
        except Exception as e:
            logger.error(f"Error in github_pr tool: {e}")
            return ToolResponse(
                success=False,
                message=f"Error: {str(e)}"
            )

    async def _get_pr_info(self, pr) -> ToolResponse:
        """Get PR metadata."""
        try:
            info = {
                "number": pr.number,
                "title": pr.title,
                "description": pr.body or "",
                "author": pr.user.login,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "commits": pr.commits,
                "comments": pr.comments,
                "review_comments": pr.review_comments,
            }

            message = f"PR #{pr.number}: {pr.title}\n"
            message += f"Author: {pr.user.login}\n"
            message += f"State: {pr.state} (Merged: {pr.merged})\n"
            message += f"Base: {pr.base.ref} ← Head: {pr.head.ref}\n"
            message += f"Changes: +{pr.additions}/-{pr.deletions} across {pr.changed_files} files\n"
            message += f"Commits: {pr.commits}, Comments: {pr.comments}, Review Comments: {pr.review_comments}"

            return ToolResponse(
                success=True,
                message=message,
                extra=ToolExtra(data=info)
            )
        except Exception as e:
            logger.error(f"Error getting PR info: {e}")
            return ToolResponse(
                success=False,
                message=f"Error getting PR info: {str(e)}"
            )

    async def _get_pr_files(self, pr) -> ToolResponse:
        """Get list of files changed in PR."""
        try:
            files = []
            for file in pr.get_files():
                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, 'patch') else None
                })

            message = f"Found {len(files)} changed files:\n"
            for f in files:
                message += f"  {f['status']}: {f['filename']} (+{f['additions']}/-{f['deletions']})\n"

            return ToolResponse(
                success=True,
                message=message.strip(),
                extra=ToolExtra(data={"files": files})
            )
        except Exception as e:
            logger.error(f"Error getting PR files: {e}")
            return ToolResponse(
                success=False,
                message=f"Error getting PR files: {str(e)}"
            )

    async def _get_pr_diff(self, pr) -> ToolResponse:
        """Get complete diff of PR."""
        try:
            files_data = []
            full_diff = ""

            for file in pr.get_files():
                if hasattr(file, 'patch') and file.patch:
                    file_diff = f"diff --git a/{file.filename} b/{file.filename}\n"
                    file_diff += f"--- a/{file.filename}\n"
                    file_diff += f"+++ b/{file.filename}\n"
                    file_diff += file.patch + "\n"
                    full_diff += file_diff

                    files_data.append({
                        "filename": file.filename,
                        "status": file.status,
                        "diff": file.patch
                    })

            message = f"Generated diff for {len(files_data)} files (total {len(full_diff)} characters)"

            return ToolResponse(
                success=True,
                message=message,
                extra=ToolExtra(data={"diff": full_diff, "files": files_data})
            )
        except Exception as e:
            logger.error(f"Error getting PR diff: {e}")
            return ToolResponse(
                success=False,
                message=f"Error getting PR diff: {str(e)}"
            )

    async def _clone_pr_branch(self, pr, repo: str, clone_path: Optional[str], token: str) -> ToolResponse:
        """Clone PR branch to local directory."""
        try:
            if clone_path is None:
                clone_path = tempfile.mkdtemp(prefix=f"pr_{pr.number}_")

            # Construct clone URL with token
            clone_url = f"https://{token}@github.com/{repo}.git"

            logger.info(f"Cloning {repo} branch {pr.head.ref} to {clone_path}")

            # Clone the repository
            repo_obj = Repo.clone_from(clone_url, clone_path, branch=pr.head.ref)

            message = f"Successfully cloned PR #{pr.number} branch '{pr.head.ref}' to {clone_path}"

            return ToolResponse(
                success=True,
                message=message,
                extra=ToolExtra(
                    file_path=clone_path,
                    data={
                        "clone_path": clone_path,
                        "branch": pr.head.ref,
                        "commit": repo_obj.head.commit.hexsha
                    }
                )
            )
        except Exception as e:
            logger.error(f"Error cloning PR branch: {e}")
            return ToolResponse(
                success=False,
                message=f"Error cloning PR branch: {str(e)}"
            )

    async def _create_pr_review(self, pr, review_body: Optional[str], review_event: str) -> ToolResponse:
        """Create a review comment on the PR."""
        try:
            if not review_body:
                return ToolResponse(
                    success=False,
                    message="review_body is required for create_pr_review action"
                )

            # Validate review_event
            valid_events = ["COMMENT", "APPROVE", "REQUEST_CHANGES"]
            if review_event not in valid_events:
                return ToolResponse(
                    success=False,
                    message=f"Invalid review_event: {review_event}. Must be one of {valid_events}"
                )

            # Create the review
            review = pr.create_review(body=review_body, event=review_event)

            message = f"Successfully created {review_event} review on PR #{pr.number}"

            return ToolResponse(
                success=True,
                message=message,
                extra=ToolExtra(data={
                    "review_id": review.id,
                    "event": review_event,
                    "body": review_body
                })
            )
        except Exception as e:
            logger.error(f"Error creating PR review: {e}")
            return ToolResponse(
                success=False,
                message=f"Error creating PR review: {str(e)}"
            )
