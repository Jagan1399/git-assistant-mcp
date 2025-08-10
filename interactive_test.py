#!/usr/bin/env python3
"""
Interactive test script for the State Scraper.

This script provides an interactive way to test different aspects of the
State Scraper without running the full test suite.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from git_assistant_mcp.core.state_scraper import StateScraper, GitCommandError


def interactive_test():
    """Interactive testing of State Scraper functionality."""
    
    print("🎯 Interactive State Scraper Test")
    print("=" * 40)
    
    # Check if we're in a Git repository
    current_dir = Path.cwd()
    if not (current_dir / ".git").exists():
        print("❌ Not in a Git repository!")
        print("Please run this from within a Git repository.")
        return
    
    print(f"✅ Found Git repository: {current_dir}")
    
    try:
        # Initialize scraper
        scraper = StateScraper()
        print("✅ State Scraper initialized")
        
        while True:
            print("\n" + "=" * 40)
            print("Choose a test option:")
            print("1. Quick status")
            print("2. File status only")
            print("3. Branch information")
            print("4. Recent commits")
            print("5. Remote information")
            print("6. Stash information")
            print("7. Full repository state")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                test_quick_status(scraper)
            elif choice == '2':
                test_file_status(scraper)
            elif choice == '3':
                test_branch_info(scraper)
            elif choice == '4':
                test_commits(scraper)
            elif choice == '5':
                test_remotes(scraper)
            elif choice == '6':
                test_stashes(scraper)
            elif choice == '7':
                test_full_state(scraper)
            elif choice == '8':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-8.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_quick_status(scraper):
    """Test quick status functionality."""
    print("\n📊 Testing Quick Status...")
    try:
        status = scraper.get_quick_status()
        print(f"✅ Quick status: {status}")
    except Exception as e:
        print(f"❌ Quick status failed: {e}")


def test_file_status(scraper):
    """Test file status parsing."""
    print("\n📁 Testing File Status...")
    try:
        # Get status output directly
        status_output = scraper._run_git_command(['status', '--porcelain'])
        if status_output:
            print("Raw status output:")
            print(status_output)
            
            # Parse it
            working_status, staging_status = scraper._parse_git_status(status_output)
            print(f"\n✅ Parsed {len(working_status)} working directory files")
            print(f"✅ Parsed {len(staging_status)} staging area files")
            
            # Show details
            if working_status:
                print("\nWorking directory files:")
                for file_status in working_status[:5]:
                    print(f"  {file_status.status}: {file_status.file_path}")
        else:
            print("✅ Working directory clean")
            
    except Exception as e:
        print(f"❌ File status test failed: {e}")


def test_branch_info(scraper):
    """Test branch information parsing."""
    print("\n🌿 Testing Branch Information...")
    try:
        branch_output = scraper._run_git_command(['branch', '-vv'])
        if branch_output:
            print("Raw branch output:")
            print(branch_output)
            
            # Parse it
            branches = scraper._parse_branches(branch_output)
            print(f"\n✅ Parsed {len(branches)} branches")
            
            # Show details
            for branch in branches:
                current = "👉" if branch.is_current else "  "
                remote_info = ""
                if branch.has_remote:
                    remote_info = f" -> {branch.remote_name}"
                    if branch.ahead_count > 0:
                        remote_info += f" ↑{branch.ahead_count}"
                    if branch.behind_count > 0:
                        remote_info += f" ↓{branch.behind_count}"
                print(f"  {current} {branch.name}{remote_info}")
        else:
            print("❌ No branch information found")
            
    except Exception as e:
        print(f"❌ Branch info test failed: {e}")


def test_commits(scraper):
    """Test commit parsing."""
    print("\n📝 Testing Commit Parsing...")
    try:
        log_output = scraper._run_git_command(['log', '--max-count=5', '--oneline', '--decorate'])
        if log_output:
            print("Raw log output:")
            print(log_output)
            
            # Parse it
            commits = scraper._parse_recent_commits(log_output)
            print(f"\n✅ Parsed {len(commits)} commits")
            
            # Show details
            for commit in commits:
                head_indicator = "👑" if commit.is_head else "  "
                print(f"  {head_indicator} {commit.short_hash} {commit.message}")
                print(f"      Author: {commit.author}")
                print(f"      Date: {commit.date}")
        else:
            print("❌ No commit information found")
            
    except Exception as e:
        print(f"❌ Commit test failed: {e}")


def test_remotes(scraper):
    """Test remote information parsing."""
    print("\n🌐 Testing Remote Information...")
    try:
        remote_output = scraper._run_git_command(['remote', '-v'])
        if remote_output:
            print("Raw remote output:")
            print(remote_output)
            
            # Parse it
            remotes = scraper._parse_remotes(remote_output)
            print(f"\n✅ Parsed {len(remotes)} remotes")
            
            # Show details
            for remote in remotes:
                push_indicator = "📤" if remote.is_default_push else "  "
                pull_indicator = "📥" if remote.is_default_pull else "  "
                print(f"  {push_indicator}{pull_indicator} {remote.name}: {remote.url}")
                print(f"      Type: {remote.url_type}")
        else:
            print("❌ No remote information found")
            
    except Exception as e:
        print(f"❌ Remote test failed: {e}")


def test_stashes(scraper):
    """Test stash information parsing."""
    print("\n💾 Testing Stash Information...")
    try:
        stash_output = scraper._run_git_command(['stash', 'list'])
        if stash_output:
            print("Raw stash output:")
            print(stash_output)
            
            # Parse it
            stashes = scraper._parse_stashes(stash_output)
            print(f"\n✅ Parsed {len(stashes)} stashes")
            
            # Show details
            for stash in stashes:
                print(f"  💾 {stash.stash_id}: {stash.description}")
                print(f"      Branch: {stash.branch}")
                print(f"      Created: {stash.created_at}")
        else:
            print("✅ No stashes found")
            
    except Exception as e:
        print(f"❌ Stash test failed: {e}")


def test_full_state(scraper):
    """Test full state scraping."""
    print("\n🔍 Testing Full State Scraping...")
    try:
        git_context = scraper.scrape_state()
        print("✅ Full state scraping completed!")
        
        # Show summary
        print(f"\n📋 Repository Summary:")
        print(f"  {git_context.get_summary()}")
        
        # Show key statistics
        print(f"\n📊 Statistics:")
        print(f"  Total files: {git_context.total_files}")
        print(f"  Modified: {git_context.modified_files}")
        print(f"  Staged: {git_context.staged_files}")
        print(f"  Untracked: {git_context.untracked_files}")
        
        # Show special states
        if git_context.has_conflicts:
            print("  ⚠️  Has conflicts")
        if git_context.is_merging:
            print("  🔄 Merge in progress")
        if git_context.is_rebasing:
            print("  🔄 Rebase in progress")
        if git_context.is_detached_head:
            print("  ⚠️  Detached HEAD")
            
    except Exception as e:
        print(f"❌ Full state test failed: {e}")


if __name__ == "__main__":
    interactive_test()
