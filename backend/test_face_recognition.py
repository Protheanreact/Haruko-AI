import os
import sys

def test_face_recognition():
    print("Testing Face Recognition Library...")
    
    try:
        import face_recognition
        import dlib
        print(f"[OK] face_recognition version: {face_recognition.__version__}")
        print(f"[OK] dlib version: {dlib.__version__}")
        print("[SUCCESS] FaceID libraries are installed and working!")
        return True
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print("\nPossible solutions:")
        print("1. Ensure 'Visual Studio Build Tools' with 'Desktop development with C++' is installed.")
        print("2. Run: pip install cmake")
        print("3. Run: pip install dlib")
        print("4. Run: pip install face_recognition")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if test_face_recognition():
        sys.exit(0)
    else:
        sys.exit(1)
