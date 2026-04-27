import subprocess
import sys


def run_backend():
    return subprocess.Popen(
        [sys.executable, "-m", "uv", "run", "uvicorn", "app.main:app", "--reload"]
    )


def run_dashboard():
    return subprocess.Popen(
        [sys.executable, "-m", "uv", "run", "streamlit", "run", "app/dashboard/streamlit_app.py"]
    )


if __name__ == "__main__":
    print("Starting backend + dashboard...")

    backend = run_backend()
    dashboard = run_dashboard()

    try:
        backend.wait()
        dashboard.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backend.terminate()
        dashboard.terminate()