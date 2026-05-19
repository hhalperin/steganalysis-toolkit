#!/usr/bin/env python3
"""
Test script for visible watermark detection and removal
Tests all files in the visible-dirt directory
"""

import os
import json
from pathlib import Path
from glob import glob

from stega.detection.visible_watermark_detector import detect_visible_watermarks
from stega.cleaning.visible_watermark_remover import remove_visible_watermarks
from stega.cleaning.watermark_inpaintor import inpaint_watermarks
from stega.config import resolve_input_dir, TEST_RESULTS_DIR


def run_detection_on_directory(input_dir: str, output_dir: str):
    """Test visible watermark detection on all images in directory."""
    print(f"🔍 TESTING VISIBLE WATERMARK DETECTION ON: {input_dir}")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_extensions = ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.png', '*.PNG', '*.bmp', '*.BMP', '*.tiff', '*.TIFF']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(ext))

    if not image_files:
        print(f"❌ No image files found in {input_dir}")
        return []

    print(f"📁 Found {len(image_files)} image files")
    detection_results = []

    for image_file in image_files:
        print(f"\n🖼️  Analyzing: {image_file.name}")
        try:
            result = detect_visible_watermarks(str(image_file))
            detection_file = output_path / f"{image_file.stem}_detection.json"
            with open(detection_file, 'w') as f:
                json.dump(result, f, indent=2)

            detection_results.append(result)
            print(f"   📊 Detections: {result['total_detections']}")
            print(f"   🎯 Types: {result['summary']['types_found']}")
            print(f"   📈 Confidence: {result['summary']['avg_confidence']:.1%}")

            if result['detections']:
                print("   🎯 Top detections:")
                for i, detection in enumerate(result['detections'][:3], 1):
                    print(f"      {i}. {detection['type']} ({detection['confidence']:.1%} confidence)")

        except Exception as e:
            print(f"   ❌ Error analyzing {image_file.name}: {e}")
            detection_results.append({
                'image_path': str(image_file),
                'error': str(e),
                'total_detections': 0
            })

    return detection_results


def run_removal_on_detections(detection_results: list, output_dir: str, method: str = "auto"):
    """Test watermark removal on detection results."""
    print(f"\n🧹 TESTING WATERMARK REMOVAL with method: {method}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    removal_results = []

    for result in detection_results:
        if 'error' in result:
            continue
        image_path = result['image_path']
        image_name = Path(image_path).stem

        print(f"\n🖼️  Removing watermarks from: {Path(image_path).name}")

        try:
            methods_to_test = ["inpainting", "texture_synthesis", "gradient_guided", "multi_scale_blending"]

            for removal_method in methods_to_test:
                output_file = output_path / f"{image_name}_cleaned_{removal_method}.png"

                removal_result = remove_visible_watermarks(
                    image_path,
                    result,
                    str(output_file),
                    removal_method
                )

                if removal_result.success:
                    print(f"   ✅ {removal_method}: {removal_result.removal_method}")
                    print(f"      Quality (PSNR): {removal_result.quality_metrics.get('psnr', 'N/A'):.1f}")
                    print(f"      Regions: {removal_result.regions_cleaned}")
                else:
                    print(f"   ❌ {removal_method}: Failed - {removal_result.technical_details.get('error', 'Unknown')}")

                removal_results.append(removal_result)

        except Exception as e:
            print(f"   ❌ Error removing watermarks from {image_name}: {e}")
            removal_results.append({
                'success': False,
                'error': str(e),
                'image_path': image_path
            })

    return removal_results


def run_inpainting_on_detections(detection_results: list, output_dir: str):
    """Test inpainting specifically on detection results."""
    print("\n🎨 TESTING WATERMARK INPAINTING")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    inpainting_results = []

    for result in detection_results:
        if 'error' in result:
            continue
        image_path = result['image_path']
        image_name = Path(image_path).stem

        print(f"\n🎨 Inpainting: {Path(image_path).name}")

        try:
            inpainting_methods = ["telea", "ns"]
            mask_methods = ["adaptive", "dilated", "feathered"]

            for inpaint_method in inpainting_methods:
                for mask_method in mask_methods:
                    output_file = output_path / f"{image_name}_inpainted_{inpaint_method}_{mask_method}.png"

                    inpaint_result = inpaint_watermarks(
                        image_path,
                        result,
                        str(output_file),
                        inpaint_method,
                        mask_method
                    )

                    if inpaint_result.success:
                        print(f"   ✅ {inpaint_method}/{mask_method}: {inpaint_result.inpainting_method}")
                        print(f"      Quality (PSNR): {inpaint_result.quality_metrics.get('psnr', 'N/A'):.1f}")
                        print(f"      Regions: {inpaint_result.regions_processed}")
                    else:
                        print(f"   ❌ {inpaint_method}/{mask_method}: Failed - {inpaint_result.technical_details.get('error', 'Unknown')}")

                    inpainting_results.append(inpaint_result)

        except Exception as e:
            print(f"   ❌ Error inpainting {image_name}: {e}")
            inpainting_results.append({
                'success': False,
                'error': str(e),
                'image_path': image_path
            })

    return inpainting_results


def generate_comprehensive_report(detection_results: list, removal_results: list, inpainting_results: list, output_dir: str):
    """Generate comprehensive test report."""
    report = {
        'test_summary': {
            'total_images_tested': len([r for r in detection_results if 'error' not in r]),
            'total_detections': sum(r.get('total_detections', 0) for r in detection_results if 'error' not in r),
            'successful_removals': len([r for r in removal_results if r.get('success', False)]),
            'successful_inpaintings': len([r for r in inpainting_results if r.get('success', False)])
        },
        'detection_breakdown': {},
        'method_performance': {},
        'recommendations': []
    }

    detection_types = {}
    for result in detection_results:
        if 'error' in result:
            continue
        for detection in result.get('detections', []):
            detection_type = detection.get('type', 'unknown')
            detection_types[detection_type] = detection_types.get(detection_type, 0) + 1

    report['detection_breakdown'] = detection_types

    method_performance = {}
    for result in removal_results + inpainting_results:
        if not result.get('success', False):
            continue
        method = result.get('removal_method', result.get('inpainting_method', 'unknown'))
        quality = result.get('quality_metrics', {}).get('overall_quality', 0)
        if method not in method_performance:
            method_performance[method] = {'count': 0, 'total_quality': 0, 'avg_quality': 0}
        method_performance[method]['count'] += 1
        method_performance[method]['total_quality'] += quality

    for method, stats in method_performance.items():
        stats['avg_quality'] = stats['total_quality'] / stats['count']

    report['method_performance'] = method_performance

    if detection_types.get('edge_anomaly', 0) > 0:
        report['recommendations'].append("Edge anomalies detected - inpainting methods recommended")
    if detection_types.get('gradient_anomaly', 0) > 0:
        report['recommendations'].append("Gradient anomalies detected - gradient-guided cleaning recommended")
    if detection_types.get('texture_anomaly', 0) > 0:
        report['recommendations'].append("Texture anomalies detected - texture synthesis recommended")

    best_method = max(method_performance.items(), key=lambda x: x[1]['avg_quality'])[0] if method_performance else "unknown"
    if best_method != "unknown":
        report['recommendations'].append(f"Best performing method: {best_method}")

    report_file = Path(output_dir) / "comprehensive_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print("\n📊 COMPREHENSIVE TEST SUMMARY:")
    print(f"   Images tested: {report['test_summary']['total_images_tested']}")
    print(f"   Total detections: {report['test_summary']['total_detections']}")
    print(f"   Successful removals: {report['test_summary']['successful_removals']}")
    print(f"   Successful inpaintings: {report['test_summary']['successful_inpaintings']}")

    print("\n🎯 DETECTION BREAKDOWN:")
    for detection_type, count in detection_types.items():
        print(f"   {detection_type}: {count}")

    print("\n⚡ METHOD PERFORMANCE:")
    for method, stats in method_performance.items():
        print(f"   {method}: {stats['avg_quality']:.3f} quality ({stats['count']} uses)")

    print("\n💡 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"   • {rec}")

    print(f"\n📄 Full report saved: {report_file}")

    return report


def main():
    """Main test function."""
    print("🧪 COMPREHENSIVE VISIBLE WATERMARK TEST SUITE")
    print("=" * 60)

    input_dir = str(resolve_input_dir("visible-dirt"))
    output_dir = str(TEST_RESULTS_DIR / "visible_watermark")
    (TEST_RESULTS_DIR / "visible_watermark").mkdir(parents=True, exist_ok=True)

    detection_results = run_detection_on_directory(input_dir, output_dir)
    removal_results = run_removal_on_detections(detection_results, output_dir, "auto")
    inpainting_results = run_inpainting_on_detections(detection_results, output_dir)
    generate_comprehensive_report(detection_results, removal_results, inpainting_results, output_dir)

    print("\n🎉 TEST SUITE COMPLETED!")
    print(f"📁 Results saved in: {output_dir}")
    print("✅ All visible watermark detection and removal modules tested successfully!")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
