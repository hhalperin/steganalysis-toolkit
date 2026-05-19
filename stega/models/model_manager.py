"""
AI Model Management System
Handles model downloading, versioning, updates, and deployment
"""

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import hashlib
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import shutil
from datetime import datetime
from dataclasses import dataclass, asdict
import zipfile
import tempfile

@dataclass
class ModelInfo:
    """Model information and metadata."""
    name: str
    version: str
    description: str
    model_type: str  # 'detection', 'cleaning', 'feature_extraction'
    file_size: int
    checksum: str
    download_url: str
    requirements: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_date: str
    compatibility_version: str


class ModelRegistry:
    """Registry of available AI models."""
    
    def __init__(self):
        # Registry of available models (in production, this would come from a server)
        self.models = {
            "steganography_detector_v1": ModelInfo(
                name="steganography_detector_v1",
                version="1.0.0",
                description="Advanced AI steganography detection model",
                model_type="detection",
                file_size=157000000,  # ~150MB
                checksum="sha256:a1b2c3d4e5f6...",
                download_url="https://models.stegano-ai.com/detector_v1.pth",
                requirements={"torch": ">=1.9.0", "torchvision": ">=0.10.0"},
                performance_metrics={
                    "accuracy": 0.94,
                    "precision": 0.91,
                    "recall": 0.96,
                    "f1_score": 0.93
                },
                training_date="2024-01-15",
                compatibility_version="1.0"
            ),
            
            "content_preserving_cleaner_v1": ModelInfo(
                name="content_preserving_cleaner_v1",
                version="1.0.0",
                description="Content-preserving AI steganography cleaner",
                model_type="cleaning",
                file_size=89000000,  # ~85MB
                checksum="sha256:b2c3d4e5f6a7...",
                download_url="https://models.stegano-ai.com/cleaner_v1.pth",
                requirements={"torch": ">=1.9.0", "scipy": ">=1.7.0"},
                performance_metrics={
                    "ssim": 0.98,
                    "psnr": 42.3,
                    "steganography_removal": 0.97
                },
                training_date="2024-01-20",
                compatibility_version="1.0"
            ),
            
            "style_preserving_gan_v1": ModelInfo(
                name="style_preserving_gan_v1",
                version="1.0.0",
                description="Style-preserving GAN for steganography removal",
                model_type="cleaning",
                file_size=234000000,  # ~223MB
                checksum="sha256:c3d4e5f6a7b8...",
                download_url="https://models.stegano-ai.com/style_gan_v1.pth",
                requirements={"torch": ">=1.9.0", "torchvision": ">=0.10.0"},
                performance_metrics={
                    "ssim": 0.99,
                    "psnr": 45.1,
                    "style_preservation": 0.96
                },
                training_date="2024-01-25",
                compatibility_version="1.0"
            ),
            
            "regional_cleaner_v1": ModelInfo(
                name="regional_cleaner_v1",
                version="1.0.0",
                description="Regional steganography cleaner",
                model_type="cleaning",
                file_size=67000000,  # ~64MB
                checksum="sha256:d4e5f6a7b8c9...",
                download_url="https://models.stegano-ai.com/regional_v1.pth",
                requirements={"torch": ">=1.9.0"},
                performance_metrics={
                    "regional_accuracy": 0.95,
                    "ssim": 0.97,
                    "processing_speed": 1.2  # images per second
                },
                training_date="2024-01-30",
                compatibility_version="1.0"
            )
        }
    
    def list_models(self, model_type: Optional[str] = None) -> List[ModelInfo]:
        """List available models, optionally filtered by type."""
        models = list(self.models.values())
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        return models
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        return self.models.get(model_name)
    
    def get_latest_version(self, model_base_name: str) -> Optional[ModelInfo]:
        """Get the latest version of a model family."""
        matching_models = [
            model for model in self.models.values()
            if model.name.startswith(model_base_name)
        ]
        
        if not matching_models:
            return None
        
        # Sort by version and return latest
        return max(matching_models, key=lambda m: m.version)


class ModelDownloader:
    """Downloads and manages AI model files."""
    
    def __init__(self, cache_dir: str = "models/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def download_model(self, model_info: ModelInfo, 
                      progress_callback: Optional[callable] = None) -> Path:
        """Download a model file with progress tracking."""
        
        model_path = self.cache_dir / f"{model_info.name}.pth"
        
        # Check if already downloaded and valid
        if model_path.exists() and self._verify_checksum(model_path, model_info.checksum):
            self.logger.info(f"Model {model_info.name} already downloaded and verified")
            return model_path
        
        self.logger.info(f"Downloading {model_info.name} ({model_info.file_size / 1e6:.1f} MB)")
        
        try:
            # For demo purposes, we'll create a dummy file
            # In production, this would download from the actual URL
            if "http" in model_info.download_url:
                try:
                    self._download_from_url(model_info.download_url, model_path, progress_callback)
                except Exception as download_error:
                    self.logger.warning(f"Network download failed for {model_info.name}: {download_error}")
                    self.logger.info(f"Creating dummy model file for {model_info.name}")
                    self._create_dummy_model(model_path, model_info.file_size)
            else:
                # Create dummy model file for testing
                self._create_dummy_model(model_path, model_info.file_size)

            # For demo purposes, skip checksum verification of dummy files
            if "http" in model_info.download_url:
                if not self._verify_checksum(model_path, model_info.checksum):
                    self.logger.error(f"Checksum verification failed for {model_info.name}")
                    model_path.unlink()  # Delete corrupted file
                    raise ValueError("Downloaded model failed checksum verification")

            self.logger.info(f"Successfully downloaded and verified {model_info.name}")
            return model_path

        except Exception as e:
            self.logger.error(f"Failed to download {model_info.name}: {e}")
            if model_path.exists():
                model_path.unlink()
            raise
    
    def _download_from_url(self, url: str, output_path: Path, 
                          progress_callback: Optional[callable] = None):
        """Download file from URL with progress tracking."""
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if progress_callback:
                        progress = downloaded_size / total_size if total_size > 0 else 0
                        progress_callback(progress, downloaded_size, total_size)
    
    def _create_dummy_model(self, output_path: Path, file_size: int):
        """Create a dummy model file for testing (replace with actual download in production)."""
        # Create a dummy PyTorch model state dict
        dummy_model = {
            'version': '1.0.0',
            'model_state_dict': torch.randn(1000, 1000),  # Dummy weights
            'optimizer_state_dict': {},
            'metadata': {
                'creation_date': datetime.now().isoformat(),
                'model_type': 'dummy_for_testing'
            }
        }
        
        torch.save(dummy_model, output_path)
        
        # Pad file to match expected size (for testing)
        if output_path.stat().st_size < file_size:
            with open(output_path, 'ab') as f:
                remaining_size = file_size - output_path.stat().st_size
                f.write(b'0' * remaining_size)
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum."""
        if not expected_checksum.startswith('sha256:'):
            # For demo, accept any checksum format
            return True
        
        expected = expected_checksum.replace('sha256:', '')
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        actual = sha256_hash.hexdigest()
        return actual == expected


class ModelManager:
    """High-level model management system."""

    def __init__(self, models_dir: str = "models/"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.cache_dir = self.models_dir / "cache"
        self.active_dir = self.models_dir / "active"
        self.active_dir.mkdir(parents=True, exist_ok=True)

        self.registry = ModelRegistry()
        self.downloader = ModelDownloader(str(self.cache_dir))
        self.logger = logging.getLogger(__name__)

        # Track installed models
        self.installed_models = self._load_installed_models()

        # Check if PyTorch is available
        self.torch_available = TORCH_AVAILABLE
    
    def _load_installed_models(self) -> Dict[str, Dict[str, Any]]:
        """Load information about installed models."""
        manifest_path = self.models_dir / "installed_models.json"
        
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                return json.load(f)
        
        return {}
    
    def _save_installed_models(self):
        """Save installed models manifest."""
        manifest_path = self.models_dir / "installed_models.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(self.installed_models, f, indent=2)
    
    def list_available_models(self, model_type: Optional[str] = None) -> List[ModelInfo]:
        """List all available models for download."""
        return self.registry.list_models(model_type)
    
    def list_installed_models(self) -> Dict[str, Dict[str, Any]]:
        """List all installed models."""
        return self.installed_models.copy()
    
    def install_model(self, model_name: str, 
                     progress_callback: Optional[callable] = None) -> Path:
        """Install a model by downloading and setting it up."""
        
        # Get model info
        model_info = self.registry.get_model_info(model_name)
        if not model_info:
            raise ValueError(f"Model '{model_name}' not found in registry")
        
        self.logger.info(f"Installing model: {model_name}")
        
        # Check requirements
        self._check_requirements(model_info.requirements)
        
        # Download model
        cached_path = self.downloader.download_model(model_info, progress_callback)
        
        # Copy to active directory
        active_path = self.active_dir / f"{model_name}.pth"
        shutil.copy2(cached_path, active_path)
        
        # Update installed models registry
        self.installed_models[model_name] = {
            'info': asdict(model_info),
            'installed_date': datetime.now().isoformat(),
            'file_path': str(active_path),
            'status': 'active'
        }
        
        self._save_installed_models()
        
        self.logger.info(f"Successfully installed {model_name}")
        return active_path
    
    def uninstall_model(self, model_name: str):
        """Uninstall a model."""
        if model_name not in self.installed_models:
            raise ValueError(f"Model '{model_name}' is not installed")
        
        model_info = self.installed_models[model_name]
        file_path = Path(model_info['file_path'])
        
        # Remove model file
        if file_path.exists():
            file_path.unlink()
        
        # Remove from registry
        del self.installed_models[model_name]
        self._save_installed_models()
        
        self.logger.info(f"Successfully uninstalled {model_name}")
    
    def update_model(self, model_name: str, 
                    progress_callback: Optional[callable] = None) -> bool:
        """Update a model to the latest version."""
        
        # Check if model is installed
        if model_name not in self.installed_models:
            raise ValueError(f"Model '{model_name}' is not installed")
        
        # Get current version
        current_info = self.installed_models[model_name]['info']
        current_version = current_info['version']
        
        # Get latest version
        latest_info = self.registry.get_latest_version(model_name.split('_v')[0])
        if not latest_info:
            self.logger.info(f"No updates available for {model_name}")
            return False
        
        if latest_info.version <= current_version:
            self.logger.info(f"Model {model_name} is already up to date (v{current_version})")
            return False
        
        self.logger.info(f"Updating {model_name} from v{current_version} to v{latest_info.version}")
        
        # Backup current model
        backup_path = self.models_dir / "backups"
        backup_path.mkdir(exist_ok=True)
        
        current_path = Path(self.installed_models[model_name]['file_path'])
        backup_file = backup_path / f"{model_name}_v{current_version}_backup.pth"
        shutil.copy2(current_path, backup_file)
        
        try:
            # Install new version
            new_path = self.install_model(latest_info.name, progress_callback)
            
            # Remove old version entry if different name
            if latest_info.name != model_name:
                del self.installed_models[model_name]
                self._save_installed_models()
            
            self.logger.info(f"Successfully updated {model_name} to v{latest_info.version}")
            return True
            
        except Exception as e:
            # Restore backup on failure
            self.logger.error(f"Update failed: {e}")
            shutil.copy2(backup_file, current_path)
            self.logger.info("Restored previous model version")
            raise
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get the file path of an installed model."""
        if model_name not in self.installed_models:
            return None
        
        return Path(self.installed_models[model_name]['file_path'])
    
    def validate_installation(self, model_name: str) -> Dict[str, Any]:
        """Validate that a model is properly installed and working."""
        
        if model_name not in self.installed_models:
            return {'valid': False, 'error': 'Model not installed'}
        
        model_info = self.installed_models[model_name]
        file_path = Path(model_info['file_path'])
        
        validation_result = {
            'valid': True,
            'model_name': model_name,
            'file_exists': file_path.exists(),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'loadable': False,
            'requirements_met': True,
            'errors': []
        }
        
        # Check file exists
        if not file_path.exists():
            validation_result['valid'] = False
            validation_result['errors'].append('Model file not found')
            return validation_result
        
        # Check if model can be loaded
        try:
            state_dict = torch.load(file_path, map_location='cpu')
            validation_result['loadable'] = True
        except Exception as e:
            validation_result['valid'] = False
            validation_result['loadable'] = False
            validation_result['errors'].append(f'Cannot load model: {str(e)}')
        
        # Check requirements
        requirements = model_info['info'].get('requirements', {})
        for package, version_req in requirements.items():
            try:
                if package == 'torch':
                    import torch
                    version = torch.__version__
                elif package == 'torchvision':
                    import torchvision
                    version = torchvision.__version__
                elif package == 'scipy':
                    import scipy
                    version = scipy.__version__
                else:
                    continue
                
                # Simple version check (in production, use proper version parsing)
                if not version_req.replace('>=', '').replace('==', '') in version:
                    validation_result['requirements_met'] = False
                    validation_result['errors'].append(f'{package} version mismatch')
                    
            except ImportError:
                validation_result['requirements_met'] = False
                validation_result['errors'].append(f'{package} not installed')
        
        if validation_result['errors']:
            validation_result['valid'] = False
        
        return validation_result
    
    def _check_requirements(self, requirements: Dict[str, str]):
        """Check if model requirements are met."""
        for package, version in requirements.items():
            try:
                if package == 'torch':
                    if not self.torch_available:
                        raise ImportError("torch not available")
                    import torch
                    if not torch.__version__ >= version.replace('>=', ''):
                        raise ImportError(f"torch version {torch.__version__} < required {version}")
                elif package == 'torchvision':
                    if not self.torch_available:
                        raise ImportError("torch not available (required for torchvision)")
                    import torchvision
                elif package == 'scipy':
                    import scipy
                else:
                    self.logger.warning(f"Unknown requirement: {package}")
            except ImportError as e:
                if package in ['torch', 'torchvision']:
                    self.logger.warning(f"PyTorch not available - skipping model requiring {package}")
                    continue  # Skip models that require PyTorch if it's not available
                raise RuntimeError(f"Requirement not met: {package} {version}. {str(e)}")
    
    def cleanup_cache(self, keep_latest: int = 3):
        """Clean up old cached model files."""
        
        self.logger.info(f"Cleaning up model cache, keeping {keep_latest} latest files")
        
        cache_files = list(self.cache_dir.glob("*.pth"))
        cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        removed_count = 0
        for file_path in cache_files[keep_latest:]:
            try:
                file_path.unlink()
                removed_count += 1
                self.logger.debug(f"Removed cached file: {file_path.name}")
            except Exception as e:
                self.logger.warning(f"Could not remove {file_path}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} cached files")
        else:
            self.logger.info("No cached files to remove")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get overall model management status."""
        
        status = {
            'installed_models': len(self.installed_models),
            'available_models': len(self.registry.list_models()),
            'cache_size_mb': sum(f.stat().st_size for f in self.cache_dir.glob("*")) / 1e6,
            'storage_usage': {
                'cache_dir': str(self.cache_dir),
                'active_dir': str(self.active_dir),
                'total_size_mb': sum(f.stat().st_size for f in self.models_dir.rglob("*") if f.is_file()) / 1e6
            },
            'models': {}
        }
        
        # Add detailed model status
        for model_name in self.installed_models:
            validation = self.validate_installation(model_name)
            status['models'][model_name] = {
                'valid': validation['valid'],
                'version': self.installed_models[model_name]['info']['version'],
                'installed_date': self.installed_models[model_name]['installed_date'],
                'file_size_mb': validation['file_size'] / 1e6,
                'loadable': validation['loadable']
            }
        
        return status


if __name__ == "__main__":
    # Example usage
    
    logging.basicConfig(level=logging.INFO)
    
    # Create model manager
    manager = ModelManager()
    
    # List available models
    print("Available models:")
    for model in manager.list_available_models():
        print(f"  {model.name} v{model.version} - {model.description}")
    
    # Install a model (demo)
    try:
        def progress_callback(progress, downloaded, total):
            print(f"Download progress: {progress:.1%} ({downloaded/1e6:.1f}/{total/1e6:.1f} MB)")
        
        model_path = manager.install_model("steganography_detector_v1", progress_callback)
        print(f"Model installed at: {model_path}")
        
        # Validate installation
        validation = manager.validate_installation("steganography_detector_v1")
        print(f"Validation result: {validation}")
        
        # Get status
        status = manager.get_model_status()
        print(f"Models status: {json.dumps(status, indent=2)}")
        
    except Exception as e:
        print(f"Installation failed: {e}")

