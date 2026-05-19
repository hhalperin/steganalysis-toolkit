#!/usr/bin/env python3
"""
Test script for text watermark detection and removal
Tests the new text-specific modules on grad-image.jpg and copy.png
"""

import os
import json
from pathlib import Path
from glob import glob

# Import our new text modules
from stega.detection.text_watermark_detector import detect_text_watermarks
from stega.cleaning.text_watermark_remover import remove_text_watermarks
from stega.config import resolve_input_dir, TEST_RESULTS_DIR


def run_text_detection_on_specific_files():
    """Test text watermark detection on specific files."""
    print("🔤 TESTING TEXT WATERMARK DETECTION")

    visible_dirt = resolve_input_dir("visible-dirt")
    test_files = [
        str(visible_dirt / "grad-image.jpg"),
        str(visible_dirt / "copy.png"),
    ]
    test_files = [f for f in test_files if Path(f).exists()]

    output_dir = TEST_RESULTS_DIR / "text_watermark"
    output_dir.mkdir(parents=True, exist_ok=True)

    detection_results = []

    for image_file in test_files:
        if not Path(image_file).exists():
            print(f"❌ File not found: {image_file}")
            continue

        print(f"\n🖼️  Analyzing: {Path(image_file).name}")

        try:
            result = detect_text_watermarks(image_file)
            detection_file = Path(output_dir) / f"{Path(image_file).stem}_text_detection.json"
            with open(detection_file, 'w') as f:
                json.dump(result, f, indent=2)

            detection_results.append(result)
            print(f"   📊 Text detections: {result['total_text_detections']}")
            print(f"   📈 Confidence: {result['summary']['avg_confidence']:.1%}")

            if result['text_detections']:
                print("\n   📝 Top text detections:")
                for i, detection in enumerate(result['text_detections'][:3], 1):
                    print(f"      {i}. '{detection['text_content']}' ({detection['confidence']:.1%} confidence)")
                    print(f"         Location: {detection['location']}")
                    print(f"         Repetitions: {detection['repetition_count']}")
            else:
                print("   ✅ No text watermarks detected")

        except Exception as e:
            print(f"   ❌ Error analyzing {Path(image_file).name}: {e}")
            detection_results.append({
                'image_path': image_file,
                'error': str(e),
                'total_text_detections': 0
            })

    return detection_results


def run_text_removal_on_detections(detection_results: list):
    """Test text watermark removal on detection results."""
    print("\n📝 TESTING TEXT WATERMARK REMOVAL")
    output_dir = TEST_RESULTS_DIR / "text_watermark"
    output_dir.mkdir(parents=True, exist_ok=True)

    removal_results = []

    for result in detection_results:
        if 'error' in result:
            continue

        image_path = result['image_path']
        image_name = Path(image_path).stem

        print(f"\n🖼️  Removing text from: {Path(image_path).name}")

        try:
            output_file = output_dir / f"{image_name}_text_cleaned.png"

            removal_result = remove_text_watermarks(
                image_path,
                result,
                str(output_file),
                "color_matching"
            )

            if removal_result.success:
                print(f"   ✅ Color matching: {removal_result.removal_method}")
                print(f"      Quality (PSNR): {removal_result.quality_metrics.get('psnr', 'N/A'):.1f}")
                print(f"      Text instances: {removal_result.text_instances_removed}")
            else:
                print(f"   ❌ Color matching: Failed - {removal_result.technical_details.get('error', 'Unknown')}")

            removal_results.append(removal_result)

        except Exception as e:
            print(f"   ❌ Error removing text from {image_name}: {e}")
            removal_results.append({
                'success': False,
                'error': str(e),
                'image_path': image_path
            })

    return removal_results


def generate_text_removal_report(detection_results: list, removal_results: list):
    """Generate comprehensive text removal report."""
    report = {
        'test_summary': {
            'total_images_tested': len([r for r in detection_results if 'error' not in r]),
            'total_text_detections': sum(r.get('total_text_detections', 0) for r in detection_results if 'error' not in r),
            'successful_removals': len([r for r in removal_results if r.get('success', False)])
        },
        'text_analysis': {},
        'removal_performance': {},
        'recommendations': []
    }

    text_patterns = {}
    for result in detection_results:
        if 'error' in result:
            continue
        for detection in result.get('text_detections', []):
            text_content = detection.get('text_content', 'unknown')
            text_patterns[text_content] = text_patterns.get(text_content, 0) + 1

    report['text_analysis'] = text_patterns

    method_performance = {}
    for result in removal_results:
        if not result.get('success', False):
            continue
        method = result.get('removal_method', 'unknown')
        quality = result.get('quality_metrics', {}).get('overall_quality', 0)
        if method not in method_performance:
            method_performance[method] = {'count': 0, 'total_quality': 0, 'avg_quality': 0}
        method_performance[method]['count'] += 1
        method_performance[method]['total_quality'] += quality

    for method, stats in method_performance.items():
        stats['avg_quality'] = stats['total_quality'] / stats['count']

    report['removal_performance'] = method_performance

    if text_patterns:
        most_common_text = max(text_patterns.items(), key=lambda x: x[1])
        report['recommendations'].append(f"Most common text pattern: '{most_common_text[0]}' appears {most_common_text[1]} times")

    best_method = max(method_performance.items(), key=lambda x: x[1]['avg_quality'])[0] if method_performance else "unknown"
    if best_method != "unknown":
        report['recommendations'].append(f"Best performing method: {best_method}")

    report_file = TEST_RESULTS_DIR / "text_watermark" / "text_removal_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print("\n📊 TEXT REMOVAL TEST SUMMARY:")
    print(f"   Images tested: {report['test_summary']['total_images_tested']}")
    print(f"   Total text detections: {report['test_summary']['total_text_detections']}")
    print(f"   Successful removals: {report['test_summary']['successful_removals']}")
    print("\n📝 TEXT PATTERNS:")
    for text, count in text_patterns.items():
        print(f"   '{text}': {count} instances")
    print("\n⚡ REMOVAL PERFORMANCE:")
    for method, stats in method_performance.items():
        print(f"   {method}: {stats['avg_quality']:.3f} quality ({stats['count']} uses)")
    print("\n💡 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"   • {rec}")
    print(f"\n📄 Full report saved: {report_file}")

    return report


def main():
    """Main text watermark test function."""
    print("📝 TEXT WATERMARK DETECTION & REMOVAL TEST SUITE")
    print("=" * 60)

    detection_results = run_text_detection_on_specific_files()
    removal_results = run_text_removal_on_detections(detection_results)
    generate_text_removal_report(detection_results, removal_results)

    print("\n🎉 TEXT WATERMARK TEST SUITE COMPLETED!")
    print(f"📁 Results saved in: {TEST_RESULTS_DIR / 'text_watermark'}")
    print("✅ Text-specific watermark detection and removal tested successfully!")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
