import asyncio
import os
import signal
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

sys.path.insert(0, BASE_DIR)


def start_frontend():
    """Start Vite dev server for the frontend in FRONTEND_DIR."""
    if not os.path.isdir(FRONTEND_DIR):
        print(f"[Frontend] Warning: frontend directory not found at {FRONTEND_DIR}")
        return None

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    print("[Frontend] Starting Vite dev server on http://localhost:5173 ...")
    try:
        proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=(sys.platform == "win32"),
        )
        return proc
    except Exception as exc:
        print(f"[Frontend] Failed to start frontend dev server: {exc}")
        return None


async def main():
    import uvicorn

    frontend_proc = start_frontend()

    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
    server = uvicorn.Server(config)

    def terminate_frontend():
        if frontend_proc and frontend_proc.poll() is None:
            print("\n[Frontend] Shutting down frontend dev server...")
            try:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)],
                        capture_output=True,
                    )
                else:
                    frontend_proc.terminate()
            except Exception as e:
                print(f"[Frontend] Error terminating frontend: {e}")

    try:
        print("\n========================================================")
        print("  SAMVEDNA / CRISISCORE UNIFIED RUNNER")
        print("  Backend API:  http://127.0.0.1:8000")
        print("  API Docs:     http://127.0.0.1:8000/docs")
        print("  Frontend Web: http://localhost:5173")
        print("========================================================\n")
        await server.serve()
    finally:
        terminate_frontend()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
