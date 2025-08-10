#!/usr/bin/env python3
"""
Test script for the State Scraper.

This script demonstrates how to use the StateScraper to gather information
from a real Git repository. Run this from within a Git repository to see
the scraper in action.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from git_assistant_mcp.core.state_scraper import StateScraper, GitCommandError
from git_assistant_mcp.config.settings import get_settings


def test_state_scraper():
    """Test the State Scraper with the current repository."""
    
    print("🧪 Testing State Scraper")
    print("=" * 50)
    
    # Get current working directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Check if we're in a Git repository
    if not (current_dir / ".git").exists():
        print("❌ Error: Not in a Git repository!")
        print("Please run this script from within a Git repository.")
        return False
    
    print("✅ Found Git repository")
    
    try:
        # Initialize the scraper
        print("\n🔧 Initializing State Scraper...")
        scraper = StateScraper()
        print("✅ State Scraper initialized successfully")
        
        # Test quick status first
        print("\n📊 Testing quick status...")
        quick_status = scraper.get_quick_status()
        print(f"Quick status: {quick_status}")
        
        # Test full state scraping
        print("\n🔍 Scraping full repository state...")
        git_context = scraper.scrape_state()
        print("✅ Full state scraping completed!")
        
        # Display the results
        print("\n📋 Repository State Summary:")
        print("-" * 30)
        print(f"Repository: {git_context.repository_path}")
        print(f"Current branch: {git_context.current_branch.name}")
        print(f"Working directory: {git_context.working_directory}")
        print(f"Total files: {git_context.total_files}")
        print(f"Modified files: {git_context.modified_files}")
        print(f"Staged files: {git_context.staged_files}")
        print(f"Untracked files: {git_context.untracked_files}")
        
        # Show special states
        if git_context.has_conflicts:
            print("⚠️  Merge conflicts detected")
        if git_context.is_merging:
            print("🔄 Merge in progress")
        if git_context.is_rebasing:
            print("🔄 Rebase in progress")
        if git_context.is_detached_head:
            print("⚠️  Detached HEAD state")
        
        # Show recent commits
        if git_context.recent_commits:
            print(f"\n📝 Recent commits ({len(git_context.recent_commits)}):")
            for commit in git_context.recent_commits[:3]:  # Show first 3
                status = "👑 HEAD" if commit.is_head else "  "
                print(f"  {status} {commit.short_hash} {commit.message}")
        
        # Show file status
        if git_context.working_directory_status:
            print(f"\n📁 Working directory status ({len(git_context.working_directory_status)} files):")
            for file_status in git_context.working_directory_status[:5]:  # Show first 5
                stage_indicator = "📦" if file_status.is_staged else "📝"
                print(f"  {stage_indicator} {file_status.status}: {file_status.file_path}")
        
        if git_context.staging_area_status:
            print(f"\n📦 Staging area status ({len(git_context.staging_area_status)} files):")
            for file_status in git_context.staging_area_status[:5]:  # Show first 5
                print(f"  📦 {file_status.status}: {file_status.file_path}")
        
        # Show branches
        if git_context.local_branches:
            print(f"\n🌿 Local branches ({len(git_context.local_branches)}):")
            for branch in git_context.local_branches:
                current_indicator = "👉" if branch.is_current else "  "
                remote_info = ""
                if branch.has_remote:
                    if branch.ahead_count > 0:
                        remote_info += f" ↑{branch.ahead_count}"
                    if branch.behind_count > 0:
                        remote_info += f" ↓{branch.behind_count}"
                    if branch.is_up_to_date:
                        remote_info += " ✓"
                print(f"  {current_indicator} {branch.name}{remote_info}")
        
        # Show remotes
        if git_context.remotes:
            print(f"\n🌐 Remotes ({len(git_context.remotes)}):")
            for remote in git_context.remotes:
                push_indicator = "📤" if remote.is_default_push else "  "
                pull_indicator = "📥" if remote.is_default_pull else "  "
                print(f"  {push_indicator}{pull_indicator} {remote.name}: {remote.url}")
        
        # Show stashes
        if git_context.stashes:
            print(f"\n💾 Stashes ({len(git_context.stashes)}):")
            for stash in git_context.stashes:
                print(f"  💾 {stash.stash_id}: {stash.description}")
        
        # Test the summary method
        print(f"\n📋 Generated Summary:")
        print(f"  {git_context.get_summary()}")
        
        print("\n✅ State Scraper test completed successfully!")
        return True
        
    except GitCommandError as e:
        print(f"❌ Git command failed: {e.command}")
        print(f"   Error: {e.error_output}")
        print(f"   Exit code: {e.return_code}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_repository(repo_path: str):
    """Test the State Scraper with a specific repository path."""
    
    print(f"🧪 Testing State Scraper with repository: {repo_path}")
    print("=" * 60)
    
    try:
        # Initialize the scraper with specific path
        scraper = StateScraper(repo_path)
        
        # Get quick status
        quick_status = scraper.get_quick_status()
        print(f"Quick status: {quick_status}")
        
        # Get full context
        git_context = scraper.scrape_state()
        print(f"✅ Successfully scraped repository: {git_context.repository_path}")
        print(f"Current branch: {git_context.current_branch.name}")
        print(f"Summary: {git_context.get_summary()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing repository {repo_path}: {e}")
        return False


def main():
    """Main test function."""
    
    print("🚀 Git Assistant MCP - State Scraper Test")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Test specific repository
        repo_path = sys.argv[1]
        if not os.path.exists(repo_path):
            print(f"❌ Repository path does not exist: {repo_path}")
            return 1
        
        success = test_specific_repository(repo_path)
    else:
        # Test current directory
        success = test_state_scraper()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
