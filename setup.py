import os
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
VENV_PATH = os.path.join(PROJECT_DIR, ".venv")  # Virtual environment path
PIP_PATH = os.path.join(VENV_PATH, "Scripts", "pip.exe")  # Windows pip inside venv
PYTHON_PATH = os.path.join(VENV_PATH, "Scripts", "python.exe")  # Python inside venv
FIXTURE_FILES = ["data.json", "fine.json"]  # JSON fixtures to load


def run_command(command):
    """Run a shell command and check for errors."""
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Error running command: {command}")
        sys.exit(1)


def check_pip():
    """Check if pip or pip3 exists."""
    print("🔍 Checking for pip...")
    result = subprocess.run(
        ["where", "pip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if "not found" in result.stdout.lower():
        print("⚠️ pip not found! Trying pip3...")
        result = subprocess.run(
            ["where", "pip3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if "not found" in result.stdout.lower():
            print("❌ pip is not installed. Install Python and pip first.")
            sys.exit(1)
    print("✅ pip is available.")


def setup_virtualenv():
    """Create the virtual environment if it does not exist."""
    if not os.path.exists(VENV_PATH):
        print("🟢 Virtual environment (.venv) not found! Creating one...")
        run_command(f"python -m venv {VENV_PATH}")
    else:
        print("✅ Virtual environment (.venv) already exists.")


def install_requirements():
    """Install dependencies from requirements.txt using venv's pip."""
    requirements_file = os.path.join(PROJECT_DIR, "requirements.txt")
    if os.path.exists(requirements_file):
        print("📦 Installing dependencies from requirements.txt...")
        run_command(f'"{PIP_PATH}" install -r "{requirements_file}"')
    else:
        print("⚠️ requirements.txt not found! Skipping dependency installation.")


def apply_migrations():
    """Run makemigrations and migrate using venv's Python."""
    print("🔄 Running makemigrations...")
    run_command(f'"{PYTHON_PATH}" manage.py makemigrations')

    print("🔄 Running migrate...")
    run_command(f'"{PYTHON_PATH}" manage.py migrate')


def load_fixtures():
    """Load initial data from JSON fixtures using venv's Python."""
    for fixture in FIXTURE_FILES:
        fixture_path = os.path.join(PROJECT_DIR, fixture)
        if os.path.exists(fixture_path):
            print(f"📂 Loading data from {fixture}...")
            run_command(f'"{PYTHON_PATH}" manage.py loaddata "{fixture}"')
        else:
            print(f"⚠️ Fixture {fixture} not found! Skipping.")


def setup_env_file():
    """Set up the .env file from template.env or prompt the user."""
    if os.path.exists(".env"):
        print(".env file already exists. Proceeding with setup.")
    elif os.path.exists("template.env"):
        configure_env = (
            input("Do you want to rename template.env to .env? (y/n): ").strip().lower()
        )
        if configure_env == "y":
            print("Renaming template.env to .env...")
            os.rename("template.env", ".env")  # Rename, but don't delete template.env
        else:
            print("You can manually configure your .env file later.")
    else:
        print(
            "⚠️ No .env or template.env file found! Please ensure to set up your environment variables."
        )


def create_or_switch_git_branch():
    """Ask user if they already have a branch or want to create a new one."""
    try:
        current_branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode()
        )
        print(f"Current branch is: {current_branch}")
    except subprocess.CalledProcessError:
        print("⚠️ Not in a Git repository.")
        return

    choice = (
        input(
            "Do you want to switch to an existing branch (e) or create a new one (c)? "
        )
        .strip()
        .lower()
    )

    if choice in ["existing", "e"]:
        branch_name = input("Enter the name of the existing branch: ").strip()
        try:
            print(f"Switching to existing branch '{branch_name}'...")
            subprocess.check_call(["git", "checkout", branch_name])
        except subprocess.CalledProcessError:
            print(f"❌ Branch '{branch_name}' does not exist.")
    elif choice in ["create", "c"]:
        branch_name = input("Enter the name for the new Git branch: ").strip()
        if branch_name:
            print(f"Creating and switching to branch '{branch_name}'...")
            subprocess.check_call(["git", "checkout", "-b", branch_name])
        else:
            print("⚠️ Branch name cannot be empty. No branch created.")
    else:
        print("⚠️ Invalid choice. No branch action taken.")


if __name__ == "__main__":
    create_or_switch_git_branch()
    check_pip()
    setup_env_file()
    setup_virtualenv()
    install_requirements()
    apply_migrations()
    load_fixtures()
    print("✅ Django setup complete!")
