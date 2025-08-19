"""Debug version of main.py with remote debugging support."""
import debugpy
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Enable remote debugging
    debugpy.listen(("0.0.0.0", 5678))
    print("⏳ VS Code debugger can now be attached, press F5 in VS Code...")
    # Uncomment the next line if you want to wait for debugger to attach
    # debugpy.wait_for_client()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for debugging
        log_level="debug"
    )
