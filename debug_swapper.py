import sys
import os

# Ensure the current directory is in python path
sys.path.append(os.getcwd())

try:
    print("Attempting to import facefusion.processors.modules.face_swapper.core...")
    import facefusion.processors.modules.face_swapper.core
    print("Import successful!")
except Exception as e:
    print(f"Import failed with error: {e}")
    import traceback
    traceback.print_exc()
