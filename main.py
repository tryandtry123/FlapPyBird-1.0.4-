import asyncio
import os
import sys

# Change the working directory to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the current directory to the path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.flappy import Flappy

if __name__ == "__main__":
    asyncio.run(Flappy().start())
