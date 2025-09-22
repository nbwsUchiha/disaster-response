"""
HuggingFace Spaces deployment for FastAPI backend.
This file is specifically configured for HF Spaces deployment.
"""

import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the main FastAPI app
from main import app

# HuggingFace Spaces expects the app to be available as 'app'
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (HF Spaces uses port 7860)
    port = int(os.environ.get("PORT", 7860))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

