"""
Watermark-specific analyzer - Facade over PNG and AI-enhanced analysis.
Delegates to png_analyzer and ai_enhanced_analyzer for watermark detection.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from core.png_analyzer import PNGForensicsAnalyzer
from detection.steganography import analyze_steganography
from detection.chunk_analyzer import analyze_png_chunks


def analyze_watermarks(file_path: str, include_ai: bool = False) -> Dict[str, Any]:
    """
    Analyze an image for watermark-related patterns (LSB, metadata, steganography).
    Thin facade over existing analyzers.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    results: Dict[str, Any] = {
        "file": str(file_path),
        "chunk_analysis": None,
        "steganography": None,
        "forensics": None,
    }

    # Chunk and steganography analysis (always run)
    try:
        results["chunk_analysis"] = analyze_png_chunks(str(path))
    except Exception as e:
        results["chunk_analysis"] = {"error": str(e)}

    try:
        results["steganography"] = analyze_steganography(str(path))
    except Exception as e:
        results["steganography"] = {"error": str(e)}

    # Full forensics via png_analyzer
    try:
        analyzer = PNGForensicsAnalyzer(str(path))
        results["forensics"] = analyzer.analyze_file()
    except Exception as e:
        results["forensics"] = {"error": str(e)}

    # Optional AI-enhanced analysis
    if include_ai:
        try:
            from core.ai_enhanced_analyzer import AIEnhancedAnalyzer
            ai_analyzer = AIEnhancedAnalyzer()
            ai_result = ai_analyzer.analyze_image(str(path))
            results["ai_analysis"] = {
                "risk_level": ai_result.overall_risk_level,
                "risk_score": ai_result.risk_score,
            }
        except ImportError:
            results["ai_analysis"] = {"error": "AI modules not available"}
        except Exception as e:
            results["ai_analysis"] = {"error": str(e)}

    return results
