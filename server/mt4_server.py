#!/usr/bin/env python3
"""Minimal MT4 API Server placeholder"""

import time
import sys

def main():
    """Keep the service running"""
    print("MT4 API Server placeholder starting on port 8000...", flush=True)
    print("This is a placeholder - actual API implementation pending", flush=True)
    
    try:
        # Keep the process alive
        while True:
            time.sleep(60)
            print("API server placeholder running...", flush=True)
    except KeyboardInterrupt:
        print("\nShutting down API server placeholder", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()