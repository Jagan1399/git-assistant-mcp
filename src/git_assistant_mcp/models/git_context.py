"""
Git Context Models for Git Assistant MCP.

This module defines Pydantic models that represent the current state of a Git repository.
These models are used to:
1. Structure Git status information from the StateScraper
2. Provide context to LLM models for generating appropriate Git commands
3. Track changes and maintain state consistency across operations
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator


class FileStatus(BaseModel):
    """
    Represents the status of a single file in the Git repository.
    
    This model captures all the information needed to understand what's happening
    with a specific file, including its current state and any changes.
    """
    
    # The file path relative to the repository root
    file_path: str = Field(
        description="Relative path of the file from repository root"
    )
    
    # Current Git status of the file (e.g., "modified", "untracked", "deleted")
    status: str = Field(
        description="Git status: modified, untracked, deleted, renamed, etc."
    )
    
    # Whether the file is staged for commit
    is_staged: bool = Field(
        description="True if file changes are staged, False if unstaged"
    )
    
    # Whether the file is tracked by Git
    is_tracked: bool = Field(
        description="True if Git is tracking this file, False for untracked files"
    )
    
    # Type of changes detected (e.g., "unstaged", "staged", "both")
    change_type: Optional[str] = Field(
        default=None,
        description="Type of changes: unstaged, staged, both, or None for untracked"
    )
    
    # Additional details about the file status
    details: Optional[str] = Field(
        default=None,
        description="Additional context about the file status (e.g., 'renamed from old_name')"
    )
    
    # Whether this file has conflicts that need resolution
    has_conflicts: bool = Field(
        default=False,
        description="True if file has merge conflicts that need manual resolution"
    )


class Commit(BaseModel):
    """
    Represents a Git commit with all relevant metadata.
    
    This model provides comprehensive information about each commit,
    which is essential for understanding repository history and context.
    """
    
    # The unique hash identifier for this commit
    hash: str = Field(
        description="Full Git commit hash (40 characters)"
    )
    
    # Short hash for display purposes (7 characters)
    short_hash: str = Field(
        description="Shortened commit hash (first 7 characters)"
    )
    
    # The commit message
    message: str = Field(
        description="Commit message describing the changes"
    )
    
    # Author of the commit
    author: str = Field(
        description="Name and email of the commit author"
    )
    
    # When the commit was created
    date: datetime = Field(
        description="Timestamp when the commit was created"
    )
    
    # Whether this commit is the current HEAD
    is_head: bool = Field(
        default=False,
        description="True if this is the current HEAD commit"
    )
    
    # Branch name this commit belongs to
    branch: Optional[str] = Field(
        default=None,
        description="Branch name this commit is on"
    )
    
    # Number of files changed in this commit
    files_changed: Optional[int] = Field(
        default=None,
        description="Number of files modified in this commit"
    )


class BranchInfo(BaseModel):
    """
    Represents information about a Git branch.
    
    This model tracks branch details including relationships to remotes
    and synchronization status.
    """
    
    # Name of the branch
    name: str = Field(
        description="Local branch name"
    )
    
    # Whether this is the currently checked out branch
    is_current: bool = Field(
        description="True if this branch is currently checked out"
    )
    
    # Whether this branch exists on the remote
    has_remote: bool = Field(
        description="True if a corresponding remote branch exists"
    )
    
    # Name of the remote branch (if it exists)
    remote_name: Optional[str] = Field(
        default=None,
        description="Name of the corresponding remote branch"
    )
    
    # How many commits ahead/behind the remote branch
    ahead_count: int = Field(
        default=0,
        description="Number of commits ahead of remote branch (positive = ahead)"
    )
    
    behind_count: int = Field(
        default=0,
        description="Number of commits behind remote branch (positive = behind)"
    )
    
    # Whether this branch is up to date with remote
    is_up_to_date: bool = Field(
        description="True if branch is synchronized with remote"
    )


class RemoteInfo(BaseModel):
    """
    Represents information about remote repositories.
    
    This model tracks remote repository details and their relationships
    to local branches.
    """
    
    # Name of the remote (usually "origin")
    name: str = Field(
        description="Remote name (e.g., 'origin', 'upstream')"
    )
    
    # URL of the remote repository
    url: str = Field(
        description="Git URL of the remote repository"
    )
    
    # Type of remote (HTTPS, SSH, etc.)
    url_type: str = Field(
        description="Type of remote URL (https, ssh, git)"
    )
    
    # Whether this is the default remote for pushing
    is_default_push: bool = Field(
        default=False,
        description="True if this is the default remote for push operations"
    )
    
    # Whether this is the default remote for pulling
    is_default_pull: bool = Field(
        default=False,
        description="True if this is the default remote for pull operations"
    )


class StashInfo(BaseModel):
    """
    Represents information about Git stash entries.
    
    This model tracks stashed changes that can be applied later.
    """
    
    # Stash identifier
    stash_id: str = Field(
        description="Stash identifier (e.g., 'stash@{0}')"
    )
    
    # Description of what was stashed
    description: str = Field(
        description="Description of the stashed changes"
    )
    
    # When the stash was created
    created_at: datetime = Field(
        description="Timestamp when the stash was created"
    )
    
    # Branch where the stash was created
    branch: str = Field(
        description="Branch name where the stash was created"
    )


class GitContext(BaseModel):
    """
    Comprehensive representation of the current Git repository state.
    
    This is the main model that combines all Git information into a single
    context object. It's used by the LLM to understand the repository state
    and generate appropriate Git commands.
    """
    
    # Basic repository information
    repository_path: str = Field(
        description="Absolute path to the Git repository root"
    )
    
    # Whether this is actually a Git repository
    is_git_repository: bool = Field(
        description="True if the path contains a valid Git repository"
    )
    
    # Current working directory relative to repository
    working_directory: str = Field(
        description="Current working directory relative to repository root"
    )
    
    # Current branch information
    current_branch: BranchInfo = Field(
        description="Information about the currently checked out branch"
    )
    
    # List of all local branches
    local_branches: List[BranchInfo] = Field(
        description="List of all local branches in the repository"
    )
    
    # List of all remote branches
    remote_branches: List[BranchInfo] = Field(
        description="List of all remote branches"
    )
    
    # Information about all remotes
    remotes: List[RemoteInfo] = Field(
        description="List of all remote repositories"
    )
    
    # Current Git status (working directory and staging area)
    working_directory_status: List[FileStatus] = Field(
        description="Status of files in the working directory"
    )
    
    staging_area_status: List[FileStatus] = Field(
        description="Status of files in the staging area"
    )
    
    # Recent commit history
    recent_commits: List[Commit] = Field(
        description="List of recent commits (default: last 5)"
    )
    
    # Stash information
    stashes: List[StashInfo] = Field(
        description="List of all stash entries"
    )
    
    # Whether there are any merge conflicts
    has_conflicts: bool = Field(
        description="True if there are unresolved merge conflicts"
    )
    
    # Whether there's an ongoing merge or rebase
    is_merging: bool = Field(
        description="True if a merge is in progress"
    )
    
    is_rebasing: bool = Field(
        description="True if a rebase is in progress"
    )
    
    # Whether the repository is in a "detached HEAD" state
    is_detached_head: bool = Field(
        description="True if HEAD is not pointing to a branch"
    )
    
    # Summary statistics for quick reference
    total_files: int = Field(
        description="Total number of files in the repository"
    )
    
    modified_files: int = Field(
        description="Number of modified files"
    )
    
    staged_files: int = Field(
        description="Number of files with staged changes"
    )
    
    untracked_files: int = Field(
        description="Number of untracked files"
    )
    
    # Timestamp when this context was captured
    captured_at: datetime = Field(
        default_factory=datetime.now,
        description="When this Git context was captured"
    )
    
    # Validation methods to ensure data consistency
    @validator('has_conflicts')
    def validate_conflicts(cls, v, values):
        """
        Validate that conflicts flag is consistent with file statuses.
        
        This ensures that if any file has conflicts, the overall
        has_conflicts flag is set to True.
        """
        if 'working_directory_status' in values:
            file_conflicts = any(
                file.has_conflicts for file in values['working_directory_status']
            )
            if file_conflicts and not v:
                return True
        return v
    
    @validator('modified_files', 'staged_files', 'untracked_files')
    def validate_file_counts(cls, v, values, field):
        """
        Validate that file counts match the actual file statuses.
        
        This ensures consistency between the summary statistics
        and the detailed file status lists.
        """
        if 'working_directory_status' in values:
            if field.name == 'modified_files':
                actual_count = len([
                    f for f in values['working_directory_status']
                    if f.status in ['modified', 'deleted', 'renamed']
                ])
                if actual_count != v:
                    return actual_count
            elif field.name == 'staged_files':
                actual_count = len([
                    f for f in values['staging_area_status']
                    if f.is_staged
                ])
                if actual_count != v:
                    return actual_count
            elif field.name == 'untracked_files':
                actual_count = len([
                    f for f in values['working_directory_status']
                    if f.status == 'untracked'
                ])
                if actual_count != v:
                    return actual_count
        return v
    
    def get_summary(self) -> str:
        """
        Generate a human-readable summary of the repository state.
        
        Returns:
            A formatted string summarizing the current Git state
        """
        summary_parts = []
        
        # Branch information
        summary_parts.append(f"On branch: {self.current_branch.name}")
        
        # Status summary
        if self.modified_files > 0:
            summary_parts.append(f"Modified: {self.modified_files} files")
        if self.staged_files > 0:
            summary_parts.append(f"Staged: {self.staged_files} files")
        if self.untracked_files > 0:
            summary_parts.append(f"Untracked: {self.untracked_files} files")
        
        # Special states
        if self.has_conflicts:
            summary_parts.append("⚠️  Merge conflicts detected")
        if self.is_merging:
            summary_parts.append("🔄 Merge in progress")
        if self.is_rebasing:
            summary_parts.append("🔄 Rebase in progress")
        if self.is_detached_head:
            summary_parts.append("⚠️  Detached HEAD state")
        
        # Remote status
        if self.current_branch.has_remote:
            if self.current_branch.ahead_count > 0:
                summary_parts.append(f"↑ {self.current_branch.ahead_count} commits ahead")
            if self.current_branch.behind_count > 0:
                summary_parts.append(f"↓ {self.current_branch.behind_count} commits behind")
        
        return " | ".join(summary_parts)
    
    def get_files_by_status(self, status: str) -> List[FileStatus]:
        """
        Get all files with a specific status.
        
        Args:
            status: The status to filter by (e.g., 'modified', 'untracked')
            
        Returns:
            List of files with the specified status
        """
        return [
            f for f in self.working_directory_status
            if f.status == status
        ]
    
    def get_staged_files(self) -> List[FileStatus]:
        """
        Get all files that are currently staged.
        
        Returns:
            List of staged files
        """
        return [
            f for f in self.staging_area_status
            if f.is_staged
        ]
    
    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are any uncommitted changes.
        
        Returns:
            True if there are modified, staged, or untracked files
        """
        return (
            self.modified_files > 0 or
            self.staged_files > 0 or
            self.untracked_files > 0
        )
