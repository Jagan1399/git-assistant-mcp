"""
State Scraper for Git Assistant MCP.

This module is responsible for gathering comprehensive information about the current
state of a Git repository. It runs various Git commands and parses their output
to create a complete GitContext object that can be used by the LLM to understand
the repository state and generate appropriate Git commands.
"""

import os
import subprocess
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

from ..models.git_context import (
    GitContext, FileStatus, Commit, BranchInfo, RemoteInfo, StashInfo
)
from ..config.settings import get_settings

# Set up logging
logger = logging.getLogger(__name__)


class GitCommandError(Exception):
    """Exception raised when Git commands fail."""
    
    def __init__(self, command: str, error_output: str, return_code: int):
        self.command = command
        self.error_output = error_output
        self.return_code = return_code
        super().__init__(f"Git command failed: {command} (exit code: {return_code})")


class StateScraper:
    """
    Scrapes and parses Git repository state information.
    
    This class is responsible for:
    1. Running Git commands to gather repository information
    2. Parsing command output into structured data
    3. Creating a comprehensive GitContext object
    4. Handling errors and edge cases gracefully
    """
    
    def __init__(self, repository_path: Optional[str] = None):
        """
        Initialize the State Scraper.
        
        Args:
            repository_path: Path to the Git repository. If None, uses current directory.
        """
        self.settings = get_settings()
        self.repository_path = Path(repository_path) if repository_path else Path.cwd()
        self.git_path = self.settings.git_path
        
        # Validate that we're in a Git repository
        if not self._is_git_repository():
            raise ValueError(f"Path {self.repository_path} is not a Git repository")
        
        logger.info(f"Initialized StateScraper for repository: {self.repository_path}")
    
    def _is_git_repository(self) -> bool:
        """
        Check if the current path is a Git repository.
        
        Returns:
            True if the path contains a .git directory
        """
        git_dir = self.repository_path / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    def _run_git_command(self, command: List[str], timeout: Optional[int] = None) -> str:
        """
        Execute a Git command and return the output.
        
        Args:
            command: List of command arguments (e.g., ['status', '--porcelain'])
            timeout: Command timeout in seconds
            
        Returns:
            Command output as string
            
        Raises:
            GitCommandError: If the command fails
        """
        # Construct full command
        full_command = [self.git_path] + command
        
        # Set working directory to repository
        cwd = str(self.repository_path)
        
        # Set timeout
        if timeout is None:
            timeout = self.settings.git_timeout
        
        try:
            logger.debug(f"Running Git command: {' '.join(full_command)}")
            
            # Execute command
            result = subprocess.run(
                full_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # We'll handle errors manually
            )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown error"
                raise GitCommandError(
                    command=' '.join(full_command),
                    error_output=error_msg,
                    return_code=result.returncode
                )
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise GitCommandError(
                command=' '.join(full_command),
                error_output="Command timed out",
                return_code=-1
            )
        except subprocess.SubprocessError as e:
            raise GitCommandError(
                command=' '.join(full_command),
                error_output=str(e),
                return_code=-1
            )
    
    def _parse_git_status(self, status_output: str) -> Tuple[List[FileStatus], List[FileStatus]]:
        """
        Parse the output of 'git status --porcelain' into FileStatus objects.
        
        Git status format:
        XY PATH
        X = status of index (staging area)
        Y = status of working tree
        
        X and Y can be:
        - M = modified
        - A = added
        - D = deleted
        - R = renamed
        - C = copied
        - U = unmerged (conflicts)
        - ? = untracked
        
        Args:
            status_output: Raw output from 'git status --porcelain'
            
        Returns:
            Tuple of (working_directory_status, staging_area_status)
        """
        working_directory_status = []
        staging_area_status = []
        
        for line in status_output.split('\n'):
            if not line.strip():
                continue
            
            # Parse status line
            status_code = line[:2]
            file_path = line[3:]
            
            # Skip if no file path
            if not file_path:
                continue
            
            # Parse status codes
            index_status = status_code[0]  # Staging area status
            working_status = status_code[1]  # Working directory status
            
            # Create FileStatus objects
            file_status = self._create_file_status(
                file_path, index_status, working_status
            )
            
            # Add to appropriate list
            if working_status != ' ':
                working_directory_status.append(file_status)
            
            if index_status != ' ':
                staging_area_status.append(file_status)
        
        return working_directory_status, staging_area_status
    
    def _create_file_status(self, file_path: str, index_status: str, working_status: str) -> FileStatus:
        """
        Create a FileStatus object from Git status codes.
        
        Args:
            file_path: Path to the file
            index_status: Status in staging area (X in XY format)
            working_status: Status in working directory (Y in XY format)
            
        Returns:
            FileStatus object with parsed information
        """
        # Determine overall status
        if index_status == ' ' and working_status == '?':
            status = "untracked"
            is_tracked = False
            is_staged = False
            change_type = None
        elif index_status == ' ' and working_status != ' ':
            status = self._get_status_description(working_status)
            is_tracked = True
            is_staged = False
            change_type = "unstaged"
        elif index_status != ' ' and working_status == ' ':
            status = self._get_status_description(index_status)
            is_tracked = True
            is_staged = True
            change_type = "staged"
        else:
            # Both have status (e.g., MM = modified in both)
            status = self._get_status_description(working_status)
            is_tracked = True
            is_staged = True
            change_type = "both"
        
        # Check for conflicts
        has_conflicts = index_status == 'U' or working_status == 'U'
        
        # Get additional details for renames/copies
        details = None
        if index_status in ['R', 'C'] or working_status in ['R', 'C']:
            details = self._get_rename_copy_details(file_path)
        
        return FileStatus(
            file_path=file_path,
            status=status,
            is_staged=is_staged,
            is_tracked=is_tracked,
            change_type=change_type,
            details=details,
            has_conflicts=has_conflicts
        )
    
    def _get_status_description(self, status_code: str) -> str:
        """
        Convert Git status code to human-readable description.
        
        Args:
            status_code: Single character status code
            
        Returns:
            Human-readable status description
        """
        status_map = {
            'M': 'modified',
            'A': 'added',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied',
            'U': 'unmerged',
            '?': 'untracked'
        }
        return status_map.get(status_code, 'unknown')
    
    def _get_rename_copy_details(self, file_path: str) -> Optional[str]:
        """
        Get additional details for renamed or copied files.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Details string or None
        """
        try:
            # For renames, Git shows "old_name -> new_name"
            if ' -> ' in file_path:
                return f"renamed from {file_path.split(' -> ')[0]}"
            return None
        except Exception:
            return None
    
    def _parse_recent_commits(self, log_output: str) -> List[Commit]:
        """
        Parse the output of 'git log' into Commit objects.
        
        Args:
            log_output: Raw output from 'git log --oneline --decorate'
            
        Returns:
            List of Commit objects
        """
        commits = []
        
        for line in log_output.split('\n'):
            if not line.strip():
                continue
            
            try:
                # Parse log line format: hash (branch) message
                # Example: "a1b2c3d (HEAD -> main) Add new feature"
                match = re.match(r'^([a-f0-9]+)\s+(?:\(([^)]+)\)\s+)?(.+)$', line)
                if match:
                    hash_value = match.group(1)
                    decorations = match.group(2) if match.group(2) else ""
                    message = match.group(3)
                    
                    # Determine if this is HEAD
                    is_head = 'HEAD' in decorations
                    
                    # Extract branch name
                    branch = None
                    if '->' in decorations:
                        branch = decorations.split('->')[1].strip()
                    elif decorations and 'HEAD' not in decorations:
                        branch = decorations
                    
                    # Get additional commit info
                    commit_info = self._get_commit_info(hash_value)
                    
                    commit = Commit(
                        hash=hash_value,
                        short_hash=hash_value[:7],
                        message=message,
                        author=commit_info.get('author', 'Unknown'),
                        date=commit_info.get('date', datetime.now()),
                        is_head=is_head,
                        branch=branch,
                        files_changed=commit_info.get('files_changed')
                    )
                    commits.append(commit)
                    
            except Exception as e:
                logger.warning(f"Failed to parse commit line: {line}, error: {e}")
                continue
        
        return commits
    
    def _get_commit_info(self, commit_hash: str) -> Dict[str, any]:
        """
        Get additional information about a specific commit.
        
        Args:
            commit_hash: Full commit hash
            
        Returns:
            Dictionary with commit metadata
        """
        try:
            # Get author and date
            author_output = self._run_git_command([
                'log', '-1', '--format=%an <%ae>|%ai', commit_hash
            ])
            
            if '|' in author_output:
                author, date_str = author_output.split('|', 1)
                
                # Parse date
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    date = datetime.now()
                
                # Get files changed count
                files_output = self._run_git_command([
                    'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash
                ])
                files_changed = len([f for f in files_output.split('\n') if f.strip()])
                
                return {
                    'author': author.strip(),
                    'date': date,
                    'files_changed': files_changed
                }
        except Exception as e:
            logger.warning(f"Failed to get commit info for {commit_hash}: {e}")
        
        return {}
    
    def _parse_branches(self, branch_output: str) -> List[BranchInfo]:
        """
        Parse the output of 'git branch' into BranchInfo objects.
        
        Args:
            branch_output: Raw output from 'git branch -vv'
            
        Returns:
            List of BranchInfo objects
        """
        branches = []
        
        for line in branch_output.split('\n'):
            if not line.strip():
                continue
            
            try:
                # Parse branch line format: * branch_name [origin/branch_name] ahead/behind
                # Example: "* main [origin/main] 2 ahead, 1 behind"
                line = line.strip()
                
                # Check if current branch
                is_current = line.startswith('* ')
                if is_current:
                    line = line[2:]  # Remove "* "
                
                # Extract branch name
                parts = line.split()
                if not parts:
                    continue
                
                branch_name = parts[0]
                
                # Parse remote tracking info
                has_remote = False
                remote_name = None
                ahead_count = 0
                behind_count = 0
                
                if len(parts) > 1 and parts[1].startswith('[') and parts[1].endswith(']'):
                    remote_info = parts[1][1:-1]  # Remove brackets
                    
                    if '/' in remote_info:
                        has_remote = True
                        remote_name = remote_info.split('/')[1]
                        
                        # Parse ahead/behind counts
                        if len(parts) > 2:
                            tracking_info = ' '.join(parts[2:])
                            ahead_match = re.search(r'(\d+)\s+ahead', tracking_info)
                            behind_match = re.search(r'(\d+)\s+behind', tracking_info)
                            
                            if ahead_match:
                                ahead_count = int(ahead_match.group(1))
                            if behind_match:
                                behind_count = int(behind_match.group(1))
                
                # Determine if up to date
                is_up_to_date = ahead_count == 0 and behind_count == 0
                
                branch_info = BranchInfo(
                    name=branch_name,
                    is_current=is_current,
                    has_remote=has_remote,
                    remote_name=remote_name,
                    ahead_count=ahead_count,
                    behind_count=behind_count,
                    is_up_to_date=is_up_to_date
                )
                branches.append(branch_info)
                
            except Exception as e:
                logger.warning(f"Failed to parse branch line: {line}, error: {e}")
                continue
        
        return branches
    
    def _parse_remotes(self, remote_output: str) -> List[RemoteInfo]:
        """
        Parse the output of 'git remote' into RemoteInfo objects.
        
        Args:
            remote_output: Raw output from 'git remote -v'
            
        Returns:
            List of RemoteInfo objects
        """
        remotes = []
        remote_data = {}
        
        for line in remote_output.split('\n'):
            if not line.strip():
                continue
            
            try:
                # Parse remote line format: remote_name url (fetch/push)
                # Example: "origin  https://github.com/user/repo.git (fetch)"
                parts = line.split()
                if len(parts) >= 3:
                    remote_name = parts[0]
                    url = parts[1]
                    operation = parts[2].strip('()')
                    
                    if remote_name not in remote_data:
                        remote_data[remote_name] = {
                            'name': remote_name,
                            'url': url,
                            'url_type': self._determine_url_type(url),
                            'is_default_push': False,
                            'is_default_pull': False
                        }
                    
                    # Mark operation types
                    if operation == 'push':
                        remote_data[remote_name]['is_default_push'] = True
                    elif operation == 'fetch':
                        remote_data[remote_name]['is_default_pull'] = True
                        
            except Exception as e:
                logger.warning(f"Failed to parse remote line: {line}, error: {e}")
                continue
        
        # Convert to RemoteInfo objects
        for remote_info in remote_data.values():
            remotes.append(RemoteInfo(**remote_info))
        
        return remotes

    def _parse_remote_branches(self, remote_branch_output: str) -> List[BranchInfo]:
        """
        Parse the output of 'git branch -r' into BranchInfo objects.
        
        Args:
            remote_branch_output: Raw output from 'git branch -r'
            
        Returns:
            List of BranchInfo objects for remote branches
        """
        remote_branches = []
        
        for line in remote_branch_output.split('\n'):
            line = line.strip()
            if not line or '->' in line:  # Skip HEAD pointers
                continue
            
            try:
                # Remote branches are listed as 'origin/branch-name'
                parts = line.split('/')
                if len(parts) >= 2:
                    remote_name = parts[0]
                    branch_name = '/'.join(parts[1:])
                    
                    branch_info = BranchInfo(
                        name=branch_name,
                        is_current=False,
                        has_remote=True,
                        remote_name=remote_name,
                        ahead_count=0,  # Not applicable for remote-only branches
                        behind_count=0, # Not applicable for remote-only branches
                        is_up_to_date=True # Assumed for remote branches
                    )
                    remote_branches.append(branch_info)
                    
            except Exception as e:
                logger.warning(f"Failed to parse remote branch line: {line}, error: {e}")
                continue
                
        return remote_branches
    
    def _determine_url_type(self, url: str) -> str:
        """
        Determine the type of Git remote URL.
        
        Args:
            url: Git remote URL
            
        Returns:
            URL type: 'https', 'ssh', or 'git'
        """
        if url.startswith('https://'):
            return 'https'
        elif url.startswith('ssh://') or '@' in url:
            return 'ssh'
        elif url.startswith('git://'):
            return 'git'
        else:
            return 'unknown'
    
    def _parse_stashes(self, stash_output: str) -> List[StashInfo]:
        """
        Parse the output of 'git stash list' into StashInfo objects.
        
        Args:
            stash_output: Raw output from 'git stash list'
            
        Returns:
            List of StashInfo objects
        """
        stashes = []
        
        for line in stash_output.split('\n'):
            if not line.strip():
                continue
            
            try:
                # Parse stash line format: stash@{n}: description
                # Example: "stash@{0}: WIP on main: a1b2c3d Add feature"
                match = re.match(r'^stash@{(\d+)}:\s+(.+)$', line)
                if match:
                    stash_id = f"stash@{{{match.group(1)}}}"
                    description = match.group(2)
                    
                    # Extract branch info from description
                    branch = "unknown"
                    if " on " in description:
                        branch = description.split(" on ")[1].split(":")[0]
                    
                    # Get stash creation time
                    created_at = self._get_stash_creation_time(stash_id)
                    
                    stash_info = StashInfo(
                        stash_id=stash_id,
                        description=description,
                        created_at=created_at,
                        branch=branch
                    )
                    stashes.append(stash_info)
                    
            except Exception as e:
                logger.warning(f"Failed to parse stash line: {line}, error: {e}")
                continue
        
        return stashes
    
    def _get_stash_creation_time(self, stash_id: str) -> datetime:
        """
        Get the creation time of a stash entry.
        
        Args:
            stash_id: Stash identifier
            
        Returns:
            Creation timestamp
        """
        try:
            # Get stash commit hash
            stash_hash = self._run_git_command(['rev-parse', stash_id])
            
            # Get commit date
            date_output = self._run_git_command([
                'log', '-1', '--format=%ai', stash_hash.strip()
            ])
            
            if date_output:
                return datetime.fromisoformat(date_output.strip().replace('Z', '+00:00'))
                
        except Exception as e:
            logger.warning(f"Failed to get stash creation time for {stash_id}: {e}")
        
        return datetime.now()
    
    def _get_special_states(self) -> Dict[str, bool]:
        """
        Check for special Git states like merge, rebase, etc.
        
        Returns:
            Dictionary with special state flags
        """
        special_states = {
            'is_merging': False,
            'is_rebasing': False,
            'is_detached_head': False
        }
        
        try:
            # Check for merge state
            merge_head = self.repository_path / ".git" / "MERGE_HEAD"
            special_states['is_merging'] = merge_head.exists()
            
            # Check for rebase state
            rebase_merge = self.repository_path / ".git" / "rebase-merge"
            rebase_apply = self.repository_path / ".git" / "rebase-apply"
            special_states['is_rebasing'] = rebase_merge.exists() or rebase_apply.exists()
            
            # Check for detached HEAD
            head_content = self._run_git_command(['rev-parse', 'HEAD'])
            branch_output = self._run_git_command(['branch', '--contains', head_content.strip()])
            special_states['is_detached_head'] = not branch_output.strip()
            
        except Exception as e:
            logger.warning(f"Failed to check special states: {e}")
        
        return special_states
    
    def scrape_state(self) -> GitContext:
        """
        Scrape the complete Git repository state.
        
        This is the main method that gathers all repository information
        and returns a comprehensive GitContext object.
        
        Returns:
            GitContext object with complete repository state
            
        Raises:
            GitCommandError: If critical Git commands fail
        """
        logger.info("Starting Git state scraping...")
        
        try:
            # Get basic repository information
            repository_path = str(self.repository_path.absolute())
            working_directory = str(Path.cwd().relative_to(self.repository_path))
            
            # Get current branch
            current_branch_output = self._run_git_command(['branch', '--show-current'])
            current_branch_name = current_branch_output.strip()
            
            # Get all branches
            branches_output = self._run_git_command(['branch', '-vv'])
            all_branches = self._parse_branches(branches_output)
            
            # Find current branch info
            current_branch = next(
                (b for b in all_branches if b.name == current_branch_name),
                BranchInfo(name=current_branch_name, is_current=True)
            )
            
            # Get remotes
            remotes_output = self._run_git_command(['remote', '-v'])
            remotes = self._parse_remotes(remotes_output)

            # Get remote branches
            remote_branches_output = self._run_git_command(['branch', '-r'])
            remote_branches = self._parse_remote_branches(remote_branches_output)
            
            # Get file status
            status_output = self._run_git_command(['status', '--porcelain'])
            working_directory_status, staging_area_status = self._parse_git_status(status_output)
            
            # Get recent commits
            log_output = self._run_git_command([
                'log', f'--max-count={self.settings.max_commits}',
                '--oneline', '--decorate'
            ])
            recent_commits = self._parse_recent_commits(log_output)
            
            # Get stashes
            stash_output = self._run_git_command(['stash', 'list'])
            stashes = self._parse_stashes(stash_output)
            
            # Check special states
            special_states = self._get_special_states()
            
            # Calculate summary statistics
            modified_files = len([f for f in working_directory_status if f.status in ['modified', 'deleted', 'renamed']])
            staged_files = len([f for f in staging_area_status if f.is_staged])
            untracked_files = len([f for f in working_directory_status if f.status == 'untracked'])
            total_files = len(working_directory_status) + len(staging_area_status)
            
            # Check for conflicts
            has_conflicts = any(f.has_conflicts for f in working_directory_status)
            
            # Create GitContext object
            git_context = GitContext(
                repository_path=repository_path,
                is_git_repository=True,
                working_directory=working_directory,
                current_branch=current_branch,
                local_branches=all_branches,
                remote_branches=remote_branches,
                remotes=remotes,
                working_directory_status=working_directory_status,
                staging_area_status=staging_area_status,
                recent_commits=recent_commits,
                stashes=stashes,
                has_conflicts=has_conflicts,
                is_merging=special_states['is_merging'],
                is_rebasing=special_states['is_rebasing'],
                is_detached_head=special_states['is_detached_head'],
                total_files=total_files,
                modified_files=modified_files,
                staged_files=staged_files,
                untracked_files=untracked_files
            )
            
            logger.info("Git state scraping completed successfully")
            return git_context
            
        except Exception as e:
            logger.error(f"Failed to scrape Git state: {e}")
            raise
    
    def get_quick_status(self) -> str:
        """
        Get a quick status summary without full scraping.
        
        Returns:
            Quick status string
        """
        try:
            status_output = self._run_git_command(['status', '--short'])
            if not status_output.strip():
                return "Working directory clean"
            
            lines = [line for line in status_output.split('\n') if line.strip()]
            return f"{len(lines)} files with changes"
            
        except Exception as e:
            logger.warning(f"Failed to get quick status: {e}")
            return "Unable to determine status"
