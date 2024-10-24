import os
import git
import sys
from pathlib import Path
import getpass
import shutil
import time
import stat
import subprocess

def remove_readonly(func, path, _):
    """Remove readonly attribute and retry operation"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_remove_git_dir(directory_path):
    """Safely remove .git directory with retries"""
    git_dir = os.path.join(directory_path, '.git')
    if os.path.exists(git_dir):
        try:
            print("Cleaning up existing .git directory...")
            shutil.rmtree(git_dir, onerror=remove_readonly)
            time.sleep(1)
        except Exception as e:
            print(f"Warning: Could not remove .git directory: {e}")
            print("Please close any applications that might be accessing the .git directory")
            input("Press Enter to continue when ready...")
            try:
                shutil.rmtree(git_dir, onerror=remove_readonly)
            except Exception as e:
                print(f"Fatal: Could not remove .git directory: {e}")
                sys.exit(1)

def run_git_command(command):
    """Run a git command and return the result and any error"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def push_to_github(directory_path, repo_name, token):
    """Initialize git repository and push to GitHub"""
    try:
        # Construct the repository URL
        repo_url = f"https://github.com/kppanic80/{repo_name}.git"
        print(f"Preparing to push to: {repo_url}")

        # Safely remove existing .git directory
        safe_remove_git_dir(directory_path)

        print("Initializing new git repository...")
        # Initialize git repository with direct command
        os.system('git init')

        print("Configuring git credentials...")
        # Set git configuration with direct commands
        os.system('git config --global user.name "kppanic80"')
        os.system('git config --global user.email "your.github.email@example.com"')

        # Create .gitignore file
        gitignore_path = os.path.join(directory_path, '.gitignore')
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write("""
.git
.gitignore
__pycache__/
*.pyc
.DS_Store
.env
venv/
                """.strip())

        print("Adding files...")
        # Add all files with direct command
        os.system('git add .')
        
        print("Creating commit...")
        os.system('git commit -m "Adding files via script"')

        print("Setting up remote...")
        # Remove existing remote if it exists
        os.system('git remote remove origin')
        
        # Configure the repository URL with credentials
        credential_url = f"https://{token}@github.com/kppanic80/{repo_name}.git"
        os.system(f'git remote add origin {credential_url}')

        print("Pushing to GitHub...")
        # Try pushing to main branch first
        push_result = os.system('git push -u origin main')
        
        if push_result != 0:
            print("Trying master branch instead...")
            push_result = os.system('git push -u origin master')
            
            if push_result != 0:
                print("Push failed on both main and master branches")
                return False

        return True

    except Exception as e:
        print(f"Error during git operations: {str(e)}")
        return False

def main():
    # Get current directory
    current_dir = os.getcwd()
    
    # Get repository name
    repo_name = input("Enter the repository name (without github.com/kppanic80/): ").strip()
    
    if not repo_name:
        print("Repository name is required!")
        return
    
    # Remove .git extension if user added it
    repo_name = repo_name.replace('.git', '')
    
    # Get GitHub personal access token
    print("\nYou need a GitHub Personal Access Token with 'repo' permissions.")
    print("You can create one at: https://github.com/settings/tokens")
    token = getpass.getpass("Enter your GitHub Personal Access Token: ")
    
    print("\nInitializing local repository and pushing files...")
    
    if push_to_github(current_dir, repo_name, token):
        print("\nSuccess! All files have been pushed to GitHub.")
        print(f"Repository URL: https://github.com/kppanic80/{repo_name}")
    else:
        print("\nFailed to push files to GitHub.")
        print("\nTroubleshooting steps:")
        print("1. Verify the repository exists at: https://github.com/kppanic80/" + repo_name)
        print("2. Make sure your Personal Access Token has these permissions:")
        print("   - repo (Full control of private repositories)")
        print("   - workflow (Optional: if you're using GitHub Actions)")
        print("3. Try generating a new token at: https://github.com/settings/tokens")
        print("4. Check that you've entered the token correctly")
        print("5. Make sure you're using the correct GitHub username")

if __name__ == "__main__":
    try:
        import git
    except ImportError:
        print("Installing required packages...")
        os.system('pip install gitpython')
        import git
    
    main()
