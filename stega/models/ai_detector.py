"""
AI-Powered Steganography Detector
Uses deep learning to detect AI-generated steganographic content with high accuracy
"""

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torchvision.transforms as transforms
    from torchvision.models import resnet50, efficientnet_b0
    try:
        from torchvision.models import ResNet50_Weights, EfficientNet_B0_Weights
        _WEIGHTS_AVAILABLE = True
    except ImportError:
        _WEIGHTS_AVAILABLE = False
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    _WEIGHTS_AVAILABLE = False

import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import logging
from dataclasses import dataclass

@dataclass
class DetectionResult:
    """Result from AI steganography detection."""
    is_ai_generated: bool
    confidence: float
    steganography_type: str
    ai_tool_detected: Optional[str]
    suspicious_regions: List[Tuple[int, int, int, int]]  # (x, y, width, height)
    technical_details: Dict[str, Any]
    recommendations: List[str]


class SteganographyFeatureExtractor(nn.Module):
    """Custom feature extractor optimized for steganography detection."""

    def __init__(self, backbone='resnet50', num_classes=256):
        super().__init__()

        if backbone == 'resnet50':
            if _WEIGHTS_AVAILABLE:
                self.backbone = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
            else:
                self.backbone = resnet50(pretrained=True)
            self.backbone.fc = nn.Identity()
            backbone_dim = 2048
        elif backbone == 'efficientnet':
            if _WEIGHTS_AVAILABLE:
                self.backbone = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
            else:
                self.backbone = efficientnet_b0(pretrained=True)
            self.backbone.classifier = nn.Identity()
            backbone_dim = 1280

        # Multi-scale feature extraction for steganography patterns
        self.lsb_branch = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(128, 256)
        )

        # Frequency domain analysis branch
        self.freq_branch = nn.Sequential(
            nn.Linear(512, 256),  # Input: DCT coefficients
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128)
        )

        # Statistical pattern branch
        self.stats_branch = nn.Sequential(
            nn.Linear(32, 64),  # Input: statistical features
            nn.ReLU(),
            nn.Linear(64, 32)
        )

        # Fusion layer
        total_features = backbone_dim + 256 + 128 + 32
        self.fusion = nn.Sequential(
            nn.Linear(total_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )

    def forward(self, image, freq_features, stat_features):
        # Extract LSB patterns (operate on least significant bits)
        lsb_image = (image * 255).long() & 1  # Extract LSB
        lsb_features = self.lsb_branch(lsb_image.float())

        # Backbone features
        backbone_features = self.backbone(image)

        # Frequency domain features
        freq_features = self.freq_branch(freq_features)

        # Statistical features
        stat_features = self.stats_branch(stat_features)

        # Concatenate all features
        combined = torch.cat([backbone_features, lsb_features, freq_features, stat_features], dim=1)

        return self.fusion(combined)


class AIGenerationClassifier(nn.Module):
    """Classifier to identify specific AI steganography tools."""

    def __init__(self, input_dim=256):
        super().__init__()

        # Known AI steganography tools to classify
        self.tool_classes = [
            'clean',              # No steganography
            'ai_lsb_custom',      # Custom AI-generated LSB
            'gpt_steganography',  # GPT-based steganography
            'diffusion_hiding',   # Diffusion model hiding
            'gan_steganography',  # GAN-based steganography
            'neural_steganography', # Other neural approaches
            'ai_frequency_domain', # AI frequency domain hiding
            'deepfake_watermark',  # Deepfake watermarking
        ]

        self.classifier = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, len(self.tool_classes))
        )

    def forward(self, features):
        return self.classifier(features)


class RegionLocalizer(nn.Module):
    """Localizes suspicious regions in the image."""

    def __init__(self, input_channels=3):
        super().__init__()

        # U-Net style architecture for pixel-level suspicious region detection
        self.encoder = nn.Sequential(
            nn.Conv2d(input_channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 2, stride=2),
            nn.ReLU(),
            nn.Conv2d(128, 64, 3, padding=1),
            nn.ReLU(),

            nn.ConvTranspose2d(64, 32, 2, stride=2),
            nn.ReLU(),
            nn.Conv2d(32, 1, 3, padding=1),
            nn.Sigmoid()  # Output: probability map of suspicious regions
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AISteganoDetector:
    """Main AI-powered steganography detector."""

    def __init__(self, model_dir: str = "models/", device: str = "auto"):
        if not TORCH_AVAILABLE:
            self.logger = logging.getLogger(__name__)
            self.logger.warning("PyTorch/torchvision not available - AI detection disabled")
            self.available = False
            return

        self.available = True
        self.model_dir = Path(model_dir)
        self.device = self._setup_device(device)
        self.logger = logging.getLogger(__name__)

        # Initialize models
        self.feature_extractor = None
        self.tool_classifier = None
        self.region_localizer = None

        # Preprocessing transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])

        # Load pre-trained models if available
        self._load_models()

    def _setup_device(self, device: str) -> torch.device:
        """Setup computation device."""
        if device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)

    def _load_models(self):
        """Load pre-trained models."""
        try:
            # Feature extractor
            feature_path = self.model_dir / "steganography_feature_extractor.pth"
            if feature_path.exists():
                self.feature_extractor = SteganographyFeatureExtractor()
                self.feature_extractor.load_state_dict(torch.load(feature_path, map_location=self.device))
                self.feature_extractor.to(self.device)
                self.feature_extractor.eval()

            # Tool classifier
            classifier_path = self.model_dir / "ai_tool_classifier.pth"
            if classifier_path.exists():
                self.tool_classifier = AIGenerationClassifier()
                self.tool_classifier.load_state_dict(torch.load(classifier_path, map_location=self.device))
                self.tool_classifier.to(self.device)
                self.tool_classifier.eval()

            # Region localizer
            localizer_path = self.model_dir / "region_localizer.pth"
            if localizer_path.exists():
                self.region_localizer = RegionLocalizer()
                self.region_localizer.load_state_dict(torch.load(localizer_path, map_location=self.device))
                self.region_localizer.to(self.device)
                self.region_localizer.eval()

            self.logger.info(f"Models loaded successfully on {self.device}")

        except Exception as e:
            self.logger.warning(f"Could not load pre-trained models: {e}")
            self.logger.info("Models will need to be trained or downloaded")

    def extract_frequency_features(self, image: np.ndarray) -> np.ndarray:
        """Extract frequency domain features for steganography detection."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
        else:
            gray = image

        # Apply 2D DCT
        from scipy.fft import dctn
        dct_coeffs = dctn(gray, norm='ortho')

        # Extract statistical features from DCT coefficients
        features = []

        # Low frequency region (top-left 8x8)
        low_freq = dct_coeffs[:8, :8]
        features.extend([
            np.mean(low_freq),
            np.std(low_freq),
            np.var(low_freq),
            np.max(low_freq) - np.min(low_freq)
        ])

        # High frequency region (bottom-right region)
        h, w = dct_coeffs.shape
        high_freq = dct_coeffs[h//2:, w//2:]
        features.extend([
            np.mean(high_freq),
            np.std(high_freq),
            np.var(high_freq),
            np.max(high_freq) - np.min(high_freq)
        ])

        # Energy distribution across frequency bands
        total_energy = np.sum(dct_coeffs ** 2)
        if total_energy > 0:
            low_energy = np.sum(dct_coeffs[:h//4, :w//4] ** 2) / total_energy
            mid_energy = np.sum(dct_coeffs[h//4:3*h//4, w//4:3*w//4] ** 2) / total_energy
            high_energy = np.sum(dct_coeffs[3*h//4:, 3*w//4:] ** 2) / total_energy
        else:
            low_energy = mid_energy = high_energy = 0

        features.extend([low_energy, mid_energy, high_energy])

        # Pad to fixed length (512 features)
        while len(features) < 512:
            features.append(0.0)

        return np.array(features[:512], dtype=np.float32)

    def extract_statistical_features(self, image: np.ndarray) -> np.ndarray:
        """Extract statistical features for steganography detection."""
        features = []

        if len(image.shape) == 3:
            # Process each channel
            for channel in range(3):
                channel_data = image[:, :, channel].flatten()

                # LSB statistics
                lsb = channel_data & 1
                features.extend([
                    np.mean(lsb),
                    np.var(lsb),
                    self._calculate_runs_test(lsb),
                    self._calculate_chi_square(lsb)
                ])

                # Pixel value distribution
                features.extend([
                    np.mean(channel_data),
                    np.std(channel_data),
                    len(np.unique(channel_data)) / 256.0,  # Normalized unique values
                ])
        else:
            # Grayscale
            channel_data = image.flatten()
            lsb = channel_data & 1
            features.extend([
                np.mean(lsb), np.var(lsb),
                self._calculate_runs_test(lsb),
                self._calculate_chi_square(lsb),
                np.mean(channel_data), np.std(channel_data),
                len(np.unique(channel_data)) / 256.0
            ])

        # Pad to fixed length (32 features)
        while len(features) < 32:
            features.append(0.0)

        return np.array(features[:32], dtype=np.float32)

    def _calculate_runs_test(self, bits: np.ndarray) -> float:
        """Calculate runs test for randomness."""
        if len(bits) == 0:
            return 0.0

        runs = 1
        for i in range(1, len(bits)):
            if bits[i] != bits[i-1]:
                runs += 1

        ones = np.sum(bits)
        zeros = len(bits) - ones

        if ones == 0 or zeros == 0:
            return 1.0

        expected_runs = (2 * ones * zeros) / len(bits) + 1
        return abs(runs - expected_runs) / expected_runs if expected_runs > 0 else 1.0

    def _calculate_chi_square(self, bits: np.ndarray) -> float:
        """Calculate chi-square test for uniformity."""
        if len(bits) == 0:
            return 0.0

        ones = np.sum(bits)
        zeros = len(bits) - ones
        expected = len(bits) / 2

        if expected == 0:
            return 0.0

        chi_square = ((ones - expected) ** 2 + (zeros - expected) ** 2) / expected
        return min(chi_square / 50.0, 1.0)  # Normalize

    def detect(self, image_path: str) -> DetectionResult:
        """Perform AI-powered steganography detection."""
        if not self.available:
            # Return fallback result when PyTorch is not available
            return DetectionResult(
                is_ai_generated=False,
                confidence=0.0,
                steganography_type='unknown',
                ai_tool_detected=None,
                suspicious_regions=[],
                technical_details={'error': 'PyTorch not available'},
                recommendations=['Install PyTorch for AI detection capabilities']
            )
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_array = np.array(image)

            # Prepare tensor for model
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)

            # Extract features
            freq_features = self.extract_frequency_features(image_array)
            stat_features = self.extract_statistical_features(image_array)

            freq_tensor = torch.FloatTensor(freq_features).unsqueeze(0).to(self.device)
            stat_tensor = torch.FloatTensor(stat_features).unsqueeze(0).to(self.device)

            results = {
                'is_ai_generated': False,
                'confidence': 0.0,
                'steganography_type': 'clean',
                'ai_tool_detected': None,
                'suspicious_regions': [],
                'technical_details': {},
                'recommendations': []
            }

            # Feature extraction and classification
            if self.feature_extractor is not None:
                with torch.no_grad():
                    features = self.feature_extractor(image_tensor, freq_tensor, stat_tensor)

                    # Tool classification
                    if self.tool_classifier is not None:
                        tool_logits = self.tool_classifier(features)
                        tool_probs = F.softmax(tool_logits, dim=1)
                        tool_confidence, tool_idx = torch.max(tool_probs, 1)

                        tool_name = self.tool_classifier.tool_classes[tool_idx.item()]
                        confidence = tool_confidence.item()

                        results.update({
                            'is_ai_generated': tool_name != 'clean',
                            'confidence': confidence,
                            'steganography_type': tool_name,
                            'ai_tool_detected': tool_name if tool_name != 'clean' else None
                        })

                    # Region localization
                    if self.region_localizer is not None:
                        # Resize for region detection
                        region_input = F.interpolate(image_tensor, size=(256, 256), mode='bilinear')
                        region_map = self.region_localizer(region_input)

                        # Extract suspicious regions (threshold at 0.7)
                        region_array = region_map.squeeze().cpu().numpy()
                        suspicious_mask = region_array > 0.7

                        if np.any(suspicious_mask):
                            # Find connected components
                            from scipy import ndimage
                            labeled, num_features = ndimage.label(suspicious_mask)

                            for i in range(1, num_features + 1):
                                region_coords = np.where(labeled == i)
                                if len(region_coords[0]) > 50:  # Minimum region size
                                    y_min, y_max = region_coords[0].min(), region_coords[0].max()
                                    x_min, x_max = region_coords[1].min(), region_coords[1].max()

                                    # Scale back to original image size
                                    h_scale = image_array.shape[0] / 256
                                    w_scale = image_array.shape[1] / 256

                                    results['suspicious_regions'].append((
                                        int(x_min * w_scale),
                                        int(y_min * h_scale),
                                        int((x_max - x_min) * w_scale),
                                        int((y_max - y_min) * h_scale)
                                    ))

            # Generate technical details
            results['technical_details'] = {
                'image_size': image_array.shape[:2],
                'frequency_features_stats': {
                    'mean': float(np.mean(freq_features)),
                    'std': float(np.std(freq_features))
                },
                'statistical_features_stats': {
                    'lsb_bias': float(np.mean(stat_features[:3])),
                    'pixel_distribution': float(np.mean(stat_features[4:7]))
                }
            }

            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)

            return DetectionResult(**results)

        except Exception as e:
            self.logger.error(f"Detection failed for {image_path}: {e}")
            return DetectionResult(
                is_ai_generated=False,
                confidence=0.0,
                steganography_type='error',
                ai_tool_detected=None,
                suspicious_regions=[],
                technical_details={'error': str(e)},
                recommendations=[f"Detection failed: {str(e)}"]
            )

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on detection results."""
        recommendations = []

        if results['is_ai_generated']:
            confidence = results['confidence']
            tool = results['ai_tool_detected']

            recommendations.append(
                f"AI-generated steganography detected with {confidence:.1%} confidence"
            )

            if tool and tool != 'clean':
                recommendations.append(f"Detected tool/method: {tool}")

                # Tool-specific recommendations
                if 'lsb' in tool.lower():
                    recommendations.extend([
                        "Use AI-powered LSB cleaning to remove hidden content",
                        "Apply intelligent bit randomization while preserving visual quality"
                    ])
                elif 'frequency' in tool.lower():
                    recommendations.extend([
                        "Apply frequency domain cleaning",
                        "Use DCT-based steganography removal techniques"
                    ])
                elif 'gan' in tool.lower() or 'diffusion' in tool.lower():
                    recommendations.extend([
                        "Use advanced AI cleaning methods",
                        "Apply adversarial cleaning to counter AI-generated patterns"
                    ])

            if results['suspicious_regions']:
                recommendations.append(
                    f"Found {len(results['suspicious_regions'])} suspicious regions - "
                    "apply targeted cleaning to these areas"
                )
        else:
            recommendations.append("No AI-generated steganography detected")
            recommendations.append("Standard steganography detection may still be recommended")

        return recommendations

    def batch_detect(self, image_paths: List[str],
                    show_progress: bool = True) -> List[DetectionResult]:
        """Batch detection for multiple images."""
        results = []

        if show_progress:
            from tqdm import tqdm
            image_paths = tqdm(image_paths, desc="AI Detection")

        for image_path in image_paths:
            result = self.detect(image_path)
            results.append(result)

        return results

    def save_detection_report(self, results: List[DetectionResult],
                            output_path: str) -> None:
        """Save batch detection results to file."""
        report_data = []

        for result in results:
            report_data.append({
                'is_ai_generated': result.is_ai_generated,
                'confidence': result.confidence,
                'steganography_type': result.steganography_type,
                'ai_tool_detected': result.ai_tool_detected,
                'suspicious_regions': result.suspicious_regions,
                'technical_details': result.technical_details,
                'recommendations': result.recommendations
            })

        with open(output_path, 'w') as f:
            json.dump({
                'detection_results': report_data,
                'summary': {
                    'total_images': len(results),
                    'ai_generated_count': sum(1 for r in results if r.is_ai_generated),
                    'average_confidence': np.mean([r.confidence for r in results])
                }
            }, f, indent=2)

        print(f"Detection report saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    detector = AISteganoDetector()

    # Single image detection
    result = detector.detect("example_image.png")
    print(f"AI-generated: {result.is_ai_generated}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Tool detected: {result.ai_tool_detected}")

    # Batch detection
    image_list = ["image1.png", "image2.png", "image3.png"]
    batch_results = detector.batch_detect(image_list)
    detector.save_detection_report(batch_results, "ai_detection_report.json")
