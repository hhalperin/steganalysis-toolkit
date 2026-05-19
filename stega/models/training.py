"""
Training Pipeline for AI Steganography Detection and Removal Models
Handles data generation, model training, and evaluation
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import torchvision.transforms as transforms
from torchvision.utils import save_image
import numpy as np
from PIL import Image, ImageDraw
import os
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from tqdm import tqdm
import matplotlib.pyplot as plt
from dataclasses import dataclass

from .ai_detector import SteganographyFeatureExtractor, AIGenerationClassifier, RegionLocalizer
from .ai_cleaner import ContentPreservingCleaner, StylePreservingGAN, RegionalCleaner, IntelligentNoiseGenerator


@dataclass
class TrainingConfig:
    """Configuration for training pipeline."""
    batch_size: int = 16
    learning_rate: float = 0.0001
    num_epochs: int = 100
    device: str = "auto"
    save_interval: int = 10
    validation_split: float = 0.2
    synthetic_data_ratio: float = 0.7  # Ratio of synthetic to real training data
    

class SyntheticSteganoDataset(Dataset):
    """Generate synthetic steganographic data for training."""
    
    def __init__(self, num_samples: int = 10000, image_size: Tuple[int, int] = (256, 256)):
        self.num_samples = num_samples
        self.image_size = image_size
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Steganography techniques to simulate
        self.stego_techniques = [
            'clean',
            'ai_lsb_custom',
            'gpt_steganography',
            'diffusion_hiding',
            'gan_steganography',
            'neural_steganography',
            'ai_frequency_domain',
            'deepfake_watermark'
        ]
        
        self.logger = logging.getLogger(__name__)
    
    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        # Generate base image
        base_image = self._generate_base_image()
        
        # Choose steganography technique
        technique = random.choice(self.stego_techniques)
        
        # Apply steganographic modification
        if technique == 'clean':
            stego_image = base_image.copy()
            label = 0
        else:
            stego_image = self._apply_steganography(base_image, technique)
            label = self.stego_techniques.index(technique)
        
        # Generate region mask for localization training
        region_mask = self._generate_region_mask(base_image, technique)
        
        # Convert to tensors
        base_tensor = self.transform(base_image)
        stego_tensor = self.transform(stego_image)
        region_tensor = torch.FloatTensor(region_mask).unsqueeze(0)
        
        # Extract features for training
        freq_features = self._extract_frequency_features(np.array(stego_image))
        stat_features = self._extract_statistical_features(np.array(stego_image))
        
        return {
            'original': base_tensor,
            'steganographic': stego_tensor,
            'label': label,
            'technique': technique,
            'region_mask': region_tensor,
            'frequency_features': torch.FloatTensor(freq_features),
            'statistical_features': torch.FloatTensor(stat_features)
        }
    
    def _generate_base_image(self) -> Image.Image:
        """Generate a realistic base image."""
        # Create diverse base images
        image_type = random.choice(['gradient', 'noise', 'geometric', 'textured'])
        
        img = Image.new('RGB', self.image_size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        if image_type == 'gradient':
            # Generate gradient image
            for x in range(self.image_size[0]):
                for y in range(self.image_size[1]):
                    r = int(255 * x / self.image_size[0])
                    g = int(255 * y / self.image_size[1])
                    b = int(255 * (x + y) / sum(self.image_size))
                    img.putpixel((x, y), (r % 256, g % 256, b % 256))
        
        elif image_type == 'noise':
            # Generate noise image
            noise_array = np.random.randint(0, 256, (*self.image_size, 3), dtype=np.uint8)
            img = Image.fromarray(noise_array)
        
        elif image_type == 'geometric':
            # Generate geometric patterns
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            for _ in range(random.randint(5, 15)):
                color = random.choice(colors)
                shape_type = random.choice(['rectangle', 'ellipse'])
                
                x1 = random.randint(0, self.image_size[0] // 2)
                y1 = random.randint(0, self.image_size[1] // 2)
                x2 = random.randint(x1, self.image_size[0])
                y2 = random.randint(y1, self.image_size[1])
                
                if shape_type == 'rectangle':
                    draw.rectangle([x1, y1, x2, y2], fill=color)
                else:
                    draw.ellipse([x1, y1, x2, y2], fill=color)
        
        elif image_type == 'textured':
            # Generate textured image with repeated patterns
            pattern_size = 32
            pattern = np.random.randint(0, 256, (pattern_size, pattern_size, 3), dtype=np.uint8)
            
            # Tile the pattern
            tiled = np.tile(pattern, 
                           (self.image_size[1] // pattern_size + 1,
                            self.image_size[0] // pattern_size + 1, 1))
            tiled = tiled[:self.image_size[1], :self.image_size[0]]
            img = Image.fromarray(tiled)
        
        return img
    
    def _apply_steganography(self, image: Image.Image, technique: str) -> Image.Image:
        """Apply specific steganographic technique to image."""
        img_array = np.array(image).copy()
        
        if technique == 'ai_lsb_custom':
            # Simulate AI-generated LSB patterns
            img_array = self._apply_ai_lsb(img_array)
        
        elif technique == 'gpt_steganography':
            # Simulate GPT-based steganography patterns
            img_array = self._apply_gpt_steganography(img_array)
        
        elif technique == 'diffusion_hiding':
            # Simulate diffusion model hiding techniques
            img_array = self._apply_diffusion_hiding(img_array)
        
        elif technique == 'gan_steganography':
            # Simulate GAN-based steganography
            img_array = self._apply_gan_steganography(img_array)
        
        elif technique == 'neural_steganography':
            # Simulate other neural steganographic approaches
            img_array = self._apply_neural_steganography(img_array)
        
        elif technique == 'ai_frequency_domain':
            # Simulate AI frequency domain hiding
            img_array = self._apply_frequency_steganography(img_array)
        
        elif technique == 'deepfake_watermark':
            # Simulate deepfake watermarking patterns
            img_array = self._apply_deepfake_watermark(img_array)
        
        return Image.fromarray(img_array)
    
    def _apply_ai_lsb(self, img_array: np.ndarray) -> np.ndarray:
        """Apply AI-generated LSB patterns."""
        # Create systematic patterns that AI might generate
        height, width = img_array.shape[:2]
        
        # Generate pseudo-intelligent pattern
        for channel in range(3):
            # Use image content to determine LSB (AI-like behavior)
            gradient_x = np.abs(np.gradient(img_array[:, :, channel].astype(float), axis=1))
            gradient_y = np.abs(np.gradient(img_array[:, :, channel].astype(float), axis=0))
            
            # Create pattern based on gradients (typical AI approach)
            pattern = ((gradient_x + gradient_y) * random.random()) > np.mean(gradient_x + gradient_y)
            lsb_pattern = pattern.astype(int)
            
            # Apply to LSB with some randomness
            mask = np.random.random((height, width)) < 0.8
            final_lsb = np.where(mask, lsb_pattern, np.random.randint(0, 2, (height, width)))
            
            img_array[:, :, channel] = (img_array[:, :, channel] & 0xFE) | final_lsb
        
        return img_array
    
    def _apply_gpt_steganography(self, img_array: np.ndarray) -> np.ndarray:
        """Apply GPT-like steganography patterns."""
        # Simulate text-to-image steganography patterns
        height, width = img_array.shape[:2]
        
        # Create linguistic-pattern-like LSB modifications
        for channel in range(3):
            # Simulate word-boundary-like patterns
            pattern = np.zeros((height, width), dtype=int)
            
            # Create "token-like" regions
            token_size = 8
            for y in range(0, height, token_size):
                for x in range(0, width, token_size):
                    # Each "token" has consistent pattern
                    token_pattern = random.randint(0, 1)
                    pattern[y:y+token_size, x:x+token_size] = token_pattern
            
            # Add some noise to make it more realistic
            noise_mask = np.random.random((height, width)) < 0.1
            pattern = np.where(noise_mask, 1 - pattern, pattern)
            
            img_array[:, :, channel] = (img_array[:, :, channel] & 0xFE) | pattern
        
        return img_array
    
    def _apply_diffusion_hiding(self, img_array: np.ndarray) -> np.ndarray:
        """Apply diffusion model hiding techniques."""
        # Simulate diffusion-based steganography
        # Add subtle noise patterns that diffusion models might create
        
        noise_strength = 0.05
        gaussian_noise = np.random.normal(0, noise_strength * 255, img_array.shape)
        
        # Apply noise primarily to LSBs
        lsb_noise = (gaussian_noise > 0).astype(int)
        
        for channel in range(3):
            img_array[:, :, channel] = (img_array[:, :, channel] & 0xFE) | lsb_noise[:, :, channel]
        
        return np.clip(img_array, 0, 255).astype(np.uint8)
    
    def _apply_gan_steganography(self, img_array: np.ndarray) -> np.ndarray:
        """Apply GAN-based steganography simulation."""
        height, width = img_array.shape[:2]
        
        # Create adversarial-like patterns
        for channel in range(3):
            # Generate patterns that look like adversarial perturbations
            x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))
            
            # Create wave-like pattern (typical of adversarial examples)
            frequency = random.uniform(0.01, 0.1)
            wave_pattern = np.sin(x_coords * frequency) * np.cos(y_coords * frequency)
            wave_pattern = (wave_pattern > 0).astype(int)
            
            img_array[:, :, channel] = (img_array[:, :, channel] & 0xFE) | wave_pattern
        
        return img_array
    
    def _apply_neural_steganography(self, img_array: np.ndarray) -> np.ndarray:
        """Apply generic neural steganography patterns."""
        # Create patterns typical of neural network outputs
        height, width = img_array.shape[:2]
        
        for channel in range(3):
            # Create locally coherent but globally pseudo-random patterns
            block_size = 16
            pattern = np.zeros((height, width), dtype=int)
            
            for y in range(0, height, block_size):
                for x in range(0, width, block_size):
                    # Each block has correlated pattern
                    block_pattern = np.random.randint(0, 2, (block_size, block_size))
                    # Apply some local correlation
                    for i in range(1, block_size):
                        for j in range(1, block_size):
                            if random.random() < 0.7:  # 70% correlation with neighbors
                                block_pattern[i, j] = block_pattern[i-1, j-1]
                    
                    end_y = min(y + block_size, height)
                    end_x = min(x + block_size, width)
                    pattern[y:end_y, x:end_x] = block_pattern[:end_y-y, :end_x-x]
            
            img_array[:, :, channel] = (img_array[:, :, channel] & 0xFE) | pattern
        
        return img_array
    
    def _apply_frequency_steganography(self, img_array: np.ndarray) -> np.ndarray:
        """Apply frequency domain steganography."""
        # Simulate DCT-based hiding
        from scipy.fft import dctn, idctn
        
        for channel in range(3):
            channel_data = img_array[:, :, channel].astype(float)
            
            # Apply DCT
            dct_coeffs = dctn(channel_data, norm='ortho')
            
            # Modify high-frequency components slightly
            h, w = dct_coeffs.shape
            high_freq_region = dct_coeffs[h//2:, w//2:]
            
            # Add small modifications to high-frequency components
            modification = np.random.normal(0, 0.1, high_freq_region.shape)
            dct_coeffs[h//2:, w//2:] += modification
            
            # Convert back
            modified_channel = idctn(dct_coeffs, norm='ortho')
            img_array[:, :, channel] = np.clip(modified_channel, 0, 255)
        
        return img_array.astype(np.uint8)
    
    def _apply_deepfake_watermark(self, img_array: np.ndarray) -> np.ndarray:
        """Apply deepfake-style watermarking."""
        height, width = img_array.shape[:2]
        
        # Create subtle periodic pattern (common in deepfake watermarking)
        for channel in range(3):
            # Create checkerboard-like pattern with low amplitude
            x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))
            
            pattern_freq = 0.05
            pattern = ((x_coords * pattern_freq).astype(int) + 
                      (y_coords * pattern_freq).astype(int)) % 2
            
            # Apply pattern to LSB with very low strength
            mask = np.random.random((height, width)) < 0.3
            pattern = np.where(mask, pattern, (img_array[:, :, channel] & 1))
            
            img_array[:, :, channel] = (img_array[:, :, channel] & 0xFE) | pattern
        
        return img_array
    
    def _generate_region_mask(self, image: Image.Image, technique: str) -> np.ndarray:
        """Generate region mask for localization training."""
        mask = np.zeros(self.image_size, dtype=np.float32)
        
        if technique == 'clean':
            return mask
        
        # Generate random suspicious regions
        num_regions = random.randint(1, 3)
        
        for _ in range(num_regions):
            # Random region size and position
            region_w = random.randint(20, self.image_size[0] // 4)
            region_h = random.randint(20, self.image_size[1] // 4)
            
            x = random.randint(0, self.image_size[0] - region_w)
            y = random.randint(0, self.image_size[1] - region_h)
            
            mask[y:y+region_h, x:x+region_w] = 1.0
        
        return mask
    
    def _extract_frequency_features(self, image: np.ndarray) -> np.ndarray:
        """Extract frequency features for training."""
        # Simplified version - extract basic DCT statistics
        if len(image.shape) == 3:
            gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
        else:
            gray = image
        
        from scipy.fft import dctn
        dct_coeffs = dctn(gray, norm='ortho')
        
        # Extract simple statistics
        features = [
            np.mean(dct_coeffs),
            np.std(dct_coeffs),
            np.var(dct_coeffs),
            np.max(dct_coeffs),
            np.min(dct_coeffs)
        ]
        
        # Pad to 512 features
        while len(features) < 512:
            features.append(0.0)
        
        return np.array(features[:512], dtype=np.float32)
    
    def _extract_statistical_features(self, image: np.ndarray) -> np.ndarray:
        """Extract statistical features for training."""
        features = []
        
        if len(image.shape) == 3:
            for channel in range(3):
                channel_data = image[:, :, channel].flatten()
                lsb = channel_data & 1
                
                features.extend([
                    np.mean(lsb),
                    np.var(lsb),
                    np.mean(channel_data),
                    np.std(channel_data)
                ])
        else:
            channel_data = image.flatten()
            lsb = channel_data & 1
            features.extend([
                np.mean(lsb), np.var(lsb),
                np.mean(channel_data), np.std(channel_data)
            ])
        
        # Pad to 32 features
        while len(features) < 32:
            features.append(0.0)
        
        return np.array(features[:32], dtype=np.float32)


class TrainingPipeline:
    """Main training pipeline for AI steganography models."""
    
    def __init__(self, config: TrainingConfig, model_dir: str = "models/"):
        self.config = config
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = self._setup_device(config.device)
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.feature_extractor = SteganographyFeatureExtractor().to(self.device)
        self.tool_classifier = AIGenerationClassifier().to(self.device)
        self.region_localizer = RegionLocalizer().to(self.device)
        self.content_cleaner = ContentPreservingCleaner().to(self.device)
        self.style_gan = StylePreservingGAN().to(self.device)
        self.regional_cleaner = RegionalCleaner().to(self.device)
        self.noise_generator = IntelligentNoiseGenerator().to(self.device)
        
        # Training history
        self.training_history = {
            'detection_loss': [],
            'cleaning_loss': [],
            'validation_loss': [],
            'detection_accuracy': [],
            'cleaning_quality': []
        }
    
    def _setup_device(self, device: str) -> torch.device:
        """Setup computation device."""
        if device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)
    
    def create_datasets(self, num_synthetic: int = 10000) -> Tuple[DataLoader, DataLoader]:
        """Create training and validation datasets."""
        
        # Create synthetic dataset
        synthetic_dataset = SyntheticSteganoDataset(
            num_samples=num_synthetic,
            image_size=(256, 256)
        )
        
        # Split into train/validation
        val_size = int(len(synthetic_dataset) * self.config.validation_split)
        train_size = len(synthetic_dataset) - val_size
        
        train_dataset, val_dataset = random_split(
            synthetic_dataset, [train_size, val_size]
        )
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )
        
        return train_loader, val_loader
    
    def train_detection_models(self, train_loader: DataLoader, val_loader: DataLoader):
        """Train detection models (feature extractor, classifier, localizer)."""
        
        self.logger.info("Training detection models...")
        
        # Optimizers
        feature_optimizer = optim.Adam(self.feature_extractor.parameters(), lr=self.config.learning_rate)
        classifier_optimizer = optim.Adam(self.tool_classifier.parameters(), lr=self.config.learning_rate)
        localizer_optimizer = optim.Adam(self.region_localizer.parameters(), lr=self.config.learning_rate)
        
        # Loss functions
        classification_loss = nn.CrossEntropyLoss()
        localization_loss = nn.BCELoss()
        
        for epoch in range(self.config.num_epochs):
            self.feature_extractor.train()
            self.tool_classifier.train()
            self.region_localizer.train()
            
            epoch_loss = 0.0
            epoch_accuracy = 0.0
            
            progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{self.config.num_epochs}")
            
            for batch_idx, batch in enumerate(progress_bar):
                # Extract batch data
                stego_images = batch['steganographic'].to(self.device)
                labels = batch['label'].to(self.device)
                region_masks = batch['region_mask'].to(self.device)
                freq_features = batch['frequency_features'].to(self.device)
                stat_features = batch['statistical_features'].to(self.device)
                
                # Zero gradients
                feature_optimizer.zero_grad()
                classifier_optimizer.zero_grad()
                localizer_optimizer.zero_grad()
                
                # Forward pass through feature extractor
                features = self.feature_extractor(stego_images, freq_features, stat_features)
                
                # Classification
                class_outputs = self.tool_classifier(features)
                class_loss = classification_loss(class_outputs, labels)
                
                # Region localization
                region_outputs = self.region_localizer(stego_images)
                region_loss = localization_loss(region_outputs, region_masks)
                
                # Combined loss
                total_loss = class_loss + region_loss
                
                # Backward pass
                total_loss.backward()
                feature_optimizer.step()
                classifier_optimizer.step()
                localizer_optimizer.step()
                
                # Statistics
                epoch_loss += total_loss.item()
                
                # Calculate accuracy
                _, predicted = torch.max(class_outputs.data, 1)
                accuracy = (predicted == labels).float().mean()
                epoch_accuracy += accuracy.item()
                
                # Update progress bar
                progress_bar.set_postfix({
                    'Loss': f'{total_loss.item():.4f}',
                    'Acc': f'{accuracy.item():.3f}'
                })
            
            # Average metrics
            avg_loss = epoch_loss / len(train_loader)
            avg_accuracy = epoch_accuracy / len(train_loader)
            
            self.training_history['detection_loss'].append(avg_loss)
            self.training_history['detection_accuracy'].append(avg_accuracy)
            
            # Validation
            val_loss, val_accuracy = self._validate_detection(val_loader, classification_loss, localization_loss)
            self.training_history['validation_loss'].append(val_loss)
            
            self.logger.info(f"Epoch {epoch+1}: Loss={avg_loss:.4f}, Acc={avg_accuracy:.3f}, Val_Loss={val_loss:.4f}, Val_Acc={val_accuracy:.3f}")
            
            # Save models periodically
            if (epoch + 1) % self.config.save_interval == 0:
                self._save_detection_models(epoch + 1)
        
        # Final save
        self._save_detection_models("final")
    
    def train_cleaning_models(self, train_loader: DataLoader, val_loader: DataLoader):
        """Train cleaning models (cleaners, noise generator)."""
        
        self.logger.info("Training cleaning models...")
        
        # Optimizers
        cleaner_optimizer = optim.Adam(self.content_cleaner.parameters(), lr=self.config.learning_rate)
        gan_optimizer = optim.Adam(self.style_gan.parameters(), lr=self.config.learning_rate)
        regional_optimizer = optim.Adam(self.regional_cleaner.parameters(), lr=self.config.learning_rate)
        noise_optimizer = optim.Adam(self.noise_generator.parameters(), lr=self.config.learning_rate)
        
        # Loss functions
        reconstruction_loss = nn.MSELoss()
        perceptual_loss = nn.L1Loss()
        
        for epoch in range(self.config.num_epochs):
            self.content_cleaner.train()
            self.style_gan.train()
            self.regional_cleaner.train()
            self.noise_generator.train()
            
            epoch_loss = 0.0
            epoch_quality = 0.0
            
            progress_bar = tqdm(train_loader, desc=f"Cleaning Epoch {epoch+1}/{self.config.num_epochs}")
            
            for batch_idx, batch in enumerate(progress_bar):
                # Extract batch data
                original_images = batch['original'].to(self.device)
                stego_images = batch['steganographic'].to(self.device)
                region_masks = batch['region_mask'].to(self.device)
                
                # Zero gradients
                cleaner_optimizer.zero_grad()
                gan_optimizer.zero_grad()
                regional_optimizer.zero_grad()
                noise_optimizer.zero_grad()
                
                # Content-preserving cleaning
                cleaned_content = self.content_cleaner(stego_images)
                content_loss = reconstruction_loss(cleaned_content, original_images)
                
                # Style-preserving cleaning
                cleaned_style = self.style_gan(stego_images)
                style_loss = reconstruction_loss(cleaned_style, original_images)
                
                # Regional cleaning
                cleaned_regional = self.regional_cleaner(stego_images, region_masks)
                regional_loss = reconstruction_loss(cleaned_regional, original_images)
                
                # Intelligent noise generation
                generated_noise = self.noise_generator(stego_images)
                noise_loss = perceptual_loss(generated_noise, torch.zeros_like(generated_noise))
                
                # Combined loss
                total_loss = content_loss + style_loss + regional_loss + 0.1 * noise_loss
                
                # Backward pass
                total_loss.backward()
                cleaner_optimizer.step()
                gan_optimizer.step()
                regional_optimizer.step()
                noise_optimizer.step()
                
                # Statistics
                epoch_loss += total_loss.item()
                
                # Calculate quality metric (simplified SSIM)
                quality = 1.0 - torch.mean((cleaned_content - original_images) ** 2)
                epoch_quality += quality.item()
                
                # Update progress bar
                progress_bar.set_postfix({
                    'Loss': f'{total_loss.item():.4f}',
                    'Quality': f'{quality.item():.3f}'
                })
            
            # Average metrics
            avg_loss = epoch_loss / len(train_loader)
            avg_quality = epoch_quality / len(train_loader)
            
            self.training_history['cleaning_loss'].append(avg_loss)
            self.training_history['cleaning_quality'].append(avg_quality)
            
            # Validation
            val_loss = self._validate_cleaning(val_loader, reconstruction_loss)
            
            self.logger.info(f"Cleaning Epoch {epoch+1}: Loss={avg_loss:.4f}, Quality={avg_quality:.3f}, Val_Loss={val_loss:.4f}")
            
            # Save models periodically
            if (epoch + 1) % self.config.save_interval == 0:
                self._save_cleaning_models(epoch + 1)
        
        # Final save
        self._save_cleaning_models("final")
    
    def _validate_detection(self, val_loader: DataLoader, class_loss_fn, region_loss_fn) -> Tuple[float, float]:
        """Validate detection models."""
        self.feature_extractor.eval()
        self.tool_classifier.eval()
        self.region_localizer.eval()
        
        total_loss = 0.0
        total_accuracy = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                stego_images = batch['steganographic'].to(self.device)
                labels = batch['label'].to(self.device)
                region_masks = batch['region_mask'].to(self.device)
                freq_features = batch['frequency_features'].to(self.device)
                stat_features = batch['statistical_features'].to(self.device)
                
                features = self.feature_extractor(stego_images, freq_features, stat_features)
                class_outputs = self.tool_classifier(features)
                region_outputs = self.region_localizer(stego_images)
                
                class_loss = class_loss_fn(class_outputs, labels)
                region_loss = region_loss_fn(region_outputs, region_masks)
                loss = class_loss + region_loss
                
                total_loss += loss.item()
                
                _, predicted = torch.max(class_outputs.data, 1)
                accuracy = (predicted == labels).float().mean()
                total_accuracy += accuracy.item()
        
        return total_loss / len(val_loader), total_accuracy / len(val_loader)
    
    def _validate_cleaning(self, val_loader: DataLoader, loss_fn) -> float:
        """Validate cleaning models."""
        self.content_cleaner.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                original_images = batch['original'].to(self.device)
                stego_images = batch['steganographic'].to(self.device)
                
                cleaned = self.content_cleaner(stego_images)
                loss = loss_fn(cleaned, original_images)
                total_loss += loss.item()
        
        return total_loss / len(val_loader)
    
    def _save_detection_models(self, epoch):
        """Save detection models."""
        torch.save(self.feature_extractor.state_dict(), 
                  self.model_dir / f"steganography_feature_extractor_epoch_{epoch}.pth")
        torch.save(self.tool_classifier.state_dict(), 
                  self.model_dir / f"ai_tool_classifier_epoch_{epoch}.pth")
        torch.save(self.region_localizer.state_dict(), 
                  self.model_dir / f"region_localizer_epoch_{epoch}.pth")
    
    def _save_cleaning_models(self, epoch):
        """Save cleaning models."""
        torch.save(self.content_cleaner.state_dict(), 
                  self.model_dir / f"content_preserving_cleaner_epoch_{epoch}.pth")
        torch.save(self.style_gan.state_dict(), 
                  self.model_dir / f"style_preserving_gan_epoch_{epoch}.pth")
        torch.save(self.regional_cleaner.state_dict(), 
                  self.model_dir / f"regional_cleaner_epoch_{epoch}.pth")
        torch.save(self.noise_generator.state_dict(), 
                  self.model_dir / f"intelligent_noise_generator_epoch_{epoch}.pth")
    
    def plot_training_history(self, save_path: str = None):
        """Plot training history."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Detection loss
        axes[0, 0].plot(self.training_history['detection_loss'], label='Train')
        axes[0, 0].plot(self.training_history['validation_loss'], label='Validation')
        axes[0, 0].set_title('Detection Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        
        # Detection accuracy
        axes[0, 1].plot(self.training_history['detection_accuracy'])
        axes[0, 1].set_title('Detection Accuracy')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('Accuracy')
        
        # Cleaning loss
        axes[1, 0].plot(self.training_history['cleaning_loss'])
        axes[1, 0].set_title('Cleaning Loss')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Loss')
        
        # Cleaning quality
        axes[1, 1].plot(self.training_history['cleaning_quality'])
        axes[1, 1].set_title('Cleaning Quality')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('Quality Score')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
    
    def full_training_pipeline(self, num_synthetic: int = 20000):
        """Run the complete training pipeline."""
        self.logger.info("Starting full AI steganography training pipeline")
        
        # Create datasets
        train_loader, val_loader = self.create_datasets(num_synthetic)
        self.logger.info(f"Created datasets: {len(train_loader.dataset)} train, {len(val_loader.dataset)} val")
        
        # Train detection models
        self.train_detection_models(train_loader, val_loader)
        
        # Train cleaning models
        self.train_cleaning_models(train_loader, val_loader)
        
        # Save training history
        history_path = self.model_dir / "training_history.json"
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        
        # Plot and save training curves
        self.plot_training_history(str(self.model_dir / "training_curves.png"))
        
        self.logger.info("Training pipeline completed successfully")
        self.logger.info(f"Models saved in: {self.model_dir}")


if __name__ == "__main__":
    # Example training run
    config = TrainingConfig(
        batch_size=8,  # Smaller batch size for limited GPU memory
        learning_rate=0.0001,
        num_epochs=50,
        save_interval=10
    )
    
    pipeline = TrainingPipeline(config)
    pipeline.full_training_pipeline(num_synthetic=5000)  # Start with smaller dataset

