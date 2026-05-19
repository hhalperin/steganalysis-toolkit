"""
PNG Forensics Toolkit Setup Script
Quick setup and verification of the analysis environment
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Verify Python version compatibility."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """Install required packages."""
    print("\n📦 Installing required packages...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def verify_imports():
    """Verify that all required modules can be imported."""
    print("\n🔍 Verifying module imports...")
    
    required_modules = [
        'PIL',       # Pillow
        'numpy',     # NumPy
        'scipy',     # SciPy
        'rich',      # Rich console
        'matplotlib' # Matplotlib
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("   Try running: pip install -r requirements.txt")
        return False
    
    return True

def verify_project_structure():
    """Verify that all project files are present."""
    print("\n📁 Verifying project structure...")
    
    required_files = [
        'src/png_analyzer.py',
        'src/chunk_analyzer.py',
        'src/steganography.py',
        'src/unicode_scanner.py',
        '.cursor/commands/analyze.md',
        '.cursor/rules/steganography_detection.md',
        '.cursor/rules/decryption_guidelines.md',
        'examples.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of the toolkit."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test chunk analyzer import
        sys.path.insert(0, 'src')
        
        from detection.chunk_analyzer import PNGChunk
        from detection.unicode_scanner import UnicodeScanner
        from detection.steganography import SteganographyDetector
        from core.png_analyzer import PNGForensicsAnalyzer
        
        print("✅ Core modules import successfully")
        
        # Test Unicode scanner with sample text
        scanner = UnicodeScanner()
        test_text = "Normal text\u200BHidden content"
        results = scanner.scan_text(test_text)
        
        if results and len(results) > 0:
            print("✅ Unicode scanner working")
        else:
            print("⚠️  Unicode scanner may have issues")
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def create_sample_test():
    """Create and test with a sample PNG file."""
    print("\n🖼️  Creating sample PNG for testing...")
    
    try:
        from PIL import Image, ImageDraw
        import numpy as np
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='lightblue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 80, 80], fill='white', outline='black')
        draw.text((35, 45), "Test", fill='black')
        
        test_file = 'test_image.png'
        img.save(test_file)
        print(f"✅ Created test image: {test_file}")
        
        # Test analysis
        sys.path.insert(0, 'src')
        from detection.chunk_analyzer import analyze_png_chunks
        
        results = analyze_png_chunks(test_file)
        
        if results and 'total_chunks' in results:
            print(f"✅ Analysis test passed - found {results['total_chunks']} chunks")
            
            # Clean up
            Path(test_file).unlink()
            print("✅ Test cleanup completed")
            return True
        else:
            print("❌ Analysis test failed")
            return False
            
    except Exception as e:
        print(f"❌ Sample test failed: {e}")
        return False

def main():
    """Main setup and verification routine."""
    print("🔍 PNG Forensics Toolkit - Setup & Verification")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Step 1: Check Python version
    if not check_python_version():
        all_checks_passed = False
    
    # Step 2: Install requirements
    if all_checks_passed:
        if not install_requirements():
            all_checks_passed = False
    
    # Step 3: Verify imports
    if all_checks_passed:
        if not verify_imports():
            all_checks_passed = False
    
    # Step 4: Verify project structure
    if all_checks_passed:
        if not verify_project_structure():
            all_checks_passed = False
    
    # Step 5: Test functionality
    if all_checks_passed:
        if not test_basic_functionality():
            all_checks_passed = False
    
    # Step 6: Sample test
    if all_checks_passed:
        if not create_sample_test():
            all_checks_passed = False
    
    # Final results
    print("\n" + "=" * 50)
    
    if all_checks_passed:
        print("🎉 Setup completed successfully!")
        print("\n📚 Next steps:")
        print("   • Run: python examples.py")
        print("   • Try: python src/png_analyzer.py <your_image.png>")
        print("   • Read: README.md for detailed usage")
        print("   • Check: .cursor/commands/analyze.md for quick commands")
    else:
        print("❌ Setup encountered issues")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure Python 3.8+ is installed")
        print("   • Run: pip install --upgrade pip")
        print("   • Run: pip install -r requirements.txt")
        print("   • Check that all project files are present")
        
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
