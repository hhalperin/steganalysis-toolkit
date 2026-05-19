"""
Advanced Pattern Identifier - Detect specific steganographic encoding schemes
Identifies exact patterns and provides targeted cleaning recommendations
"""

import numpy as np
from PIL import Image
import binascii


class AdvancedPatternDetector:
    """Identify specific steganographic patterns and encoding schemes."""
    
    def __init__(self):
        self.common_patterns = {
            'all_ones_lsb': lambda lsb: np.mean(lsb) > 0.95,
            'all_zeros_lsb': lambda lsb: np.mean(lsb) < 0.05,
            'alternating_lsb': self._detect_alternating,
            'fibonacci_sequence': self._detect_fibonacci,
            'binary_message': self._detect_binary_message,
            'steghide_signature': self._detect_steghide_signature
        }
    
    def analyze_encoding_scheme(self, image_path):
        """Identify the specific encoding scheme used."""
        print(f"🔬 ADVANCED PATTERN ANALYSIS: {image_path}")
        
        img = Image.open(image_path).convert('RGB')
        data = np.array(img)
        
        # Extract LSB data
        lsb_r = data[:, :, 0] & 1
        lsb_g = data[:, :, 1] & 1
        lsb_b = data[:, :, 2] & 1
        
        results = {}
        
        # Test each pattern
        for pattern_name, pattern_func in self.common_patterns.items():
            r_match = pattern_func(lsb_r.flatten())
            g_match = pattern_func(lsb_g.flatten())
            b_match = pattern_func(lsb_b.flatten())
            
            results[pattern_name] = {
                'r_channel': r_match,
                'g_channel': g_match,
                'b_channel': b_match,
                'all_channels': r_match and g_match and b_match
            }
        
        # Analyze white pixel encoding specifically
        white_analysis = self._analyze_white_pixel_encoding(data)
        results['white_pixel_encoding'] = white_analysis
        
        # Check for specific tool signatures
        tool_signatures = self._detect_tool_signatures(data)
        results['tool_signatures'] = tool_signatures
        
        return results
    
    def _detect_alternating(self, lsb_data):
        """Detect alternating 0,1,0,1 pattern."""
        if len(lsb_data) < 10:
            return False
        
        # Check first 100 bits for alternating pattern
        sample = lsb_data[:100]
        alternating_count = 0
        
        for i in range(len(sample) - 1):
            if sample[i] != sample[i + 1]:
                alternating_count += 1
        
        # Should be close to 50% if alternating
        return alternating_count > len(sample) * 0.8
    
    def _detect_fibonacci(self, lsb_data):
        """Detect Fibonacci sequence in LSB."""
        fib_pattern = [1, 1, 0, 1, 1, 0, 1, 1]  # Fibonacci mod 2
        if len(lsb_data) < len(fib_pattern):
            return False
        
        # Check if the pattern repeats
        for start in range(0, min(len(lsb_data) - len(fib_pattern), 50), len(fib_pattern)):
            segment = lsb_data[start:start + len(fib_pattern)]
            if np.array_equal(segment, fib_pattern):
                return True
        
        return False
    
    def _detect_binary_message(self, lsb_data):
        """Try to detect ASCII text in LSB data."""
        # Convert LSB to bytes and check for readable text
        if len(lsb_data) < 64:
            return False
        
        text_chars = []
        for i in range(0, min(len(lsb_data), 200), 8):
            if i + 8 <= len(lsb_data):
                byte_val = 0
                for j in range(8):
                    byte_val += lsb_data[i + j] << j
                
                if 32 <= byte_val <= 126:  # Printable ASCII
                    text_chars.append(chr(byte_val))
                else:
                    break
        
        # If we found at least 3 consecutive printable characters
        return len(text_chars) >= 3
    
    def _detect_steghide_signature(self, lsb_data):
        """Detect steghide tool signature patterns."""
        # Steghide typically creates more random-looking LSB patterns
        if len(lsb_data) < 1000:
            return False
        
        # Check for steghide's characteristic randomness
        sample = lsb_data[:1000]
        ones_ratio = np.mean(sample)
        
        # Steghide usually creates patterns close to 0.5 but not exactly
        return 0.45 <= ones_ratio <= 0.55 and ones_ratio != 0.5
    
    def _analyze_white_pixel_encoding(self, data):
        """Detailed analysis of white pixel encoding schemes."""
        white_mask = np.all(data > 250, axis=2)
        
        if np.sum(white_mask) < 100:
            return {'found': False}
        
        white_pixels = data[white_mask]
        
        # Check for specific encoding patterns
        encoding_patterns = {
            'uniform_lsb': self._check_uniform_lsb(white_pixels),
            'stepped_encoding': self._check_stepped_encoding(white_pixels),
            'channel_specific': self._check_channel_specific_encoding(white_pixels)
        }
        
        return {
            'found': True,
            'pixel_count': len(white_pixels),
            'patterns': encoding_patterns
        }
    
    def _check_uniform_lsb(self, pixels):
        """Check if all LSBs are the same (all 0s or all 1s)."""
        for channel in range(3):
            lsb = pixels[:, channel] & 1
            if np.all(lsb == 1) or np.all(lsb == 0):
                return True
        return False
    
    def _check_stepped_encoding(self, pixels):
        """Check for stepped encoding (251,252,253,254,255 pattern)."""
        for channel in range(3):
            unique_vals = np.unique(pixels[:, channel])
            if len(unique_vals) >= 4:
                # Check if sequential
                if np.all(np.diff(unique_vals) == 1):
                    return True
        return False
    
    def _check_channel_specific_encoding(self, pixels):
        """Check if different channels have different encoding."""
        r_unique = len(np.unique(pixels[:, 0]))
        g_unique = len(np.unique(pixels[:, 1]))
        b_unique = len(np.unique(pixels[:, 2]))
        
        # If channels have very different numbers of unique values
        return max(r_unique, g_unique, b_unique) - min(r_unique, g_unique, b_unique) > 2
    
    def _detect_tool_signatures(self, data):
        """Detect signatures of specific steganography tools."""
        signatures = {
            'canva_renderer': self._detect_canva_signature(data),
            'photoshop_layers': self._detect_photoshop_signature(data),
            'ai_generation': self._detect_ai_signature(data)
        }
        
        return signatures
    
    def _detect_canva_signature(self, data):
        """Detect Canva rendering artifacts that might contain tracking."""
        # Canva often creates very uniform LSB patterns
        lsb_data = data & 1
        uniformity = np.std(lsb_data)
        
        # Very low standard deviation indicates uniform LSB (suspicious)
        return uniformity < 0.2
    
    def _detect_photoshop_signature(self, data):
        """Detect Photoshop layer artifacts."""
        # Check for layer blend artifacts in LSB
        height, width = data.shape[:2]
        
        # Sample corners for blend artifacts
        corners = [
            data[0:10, 0:10],  # Top-left
            data[0:10, -10:],  # Top-right
            data[-10:, 0:10],  # Bottom-left
            data[-10:, -10:]   # Bottom-right
        ]
        
        for corner in corners:
            lsb = corner & 1
            if np.std(lsb) < 0.1:  # Very uniform LSB in corners
                return True
        
        return False
    
    def _detect_ai_signature(self, data):
        """Detect AI generation signatures."""
        # AI-generated images often have specific noise patterns
        # Check for too-perfect gradients in LSB
        lsb_r = data[:, :, 0] & 1
        
        # Calculate local variance in LSB
        from scipy import ndimage
        variance_map = ndimage.uniform_filter(lsb_r.astype(float), size=5)
        
        # AI images often have very low variance in LSB
        avg_variance = np.mean(variance_map)
        return avg_variance > 0.8 or avg_variance < 0.2


def create_cleaning_strategy(patterns):
    """Create a targeted cleaning strategy based on detected patterns."""
    strategy = {
        'method': 'lsb_natural',
        'target_channels': [0, 1, 2],
        'preserve_quality': 0.98,
        'specific_actions': []
    }
    
    # Analyze patterns and adjust strategy
    if patterns.get('lsb_bias', {}).get('suspicious'):
        bias_data = patterns['lsb_bias']
        if bias_data['r_bias'] > 0.9:
            strategy['specific_actions'].append('Randomize R-channel LSB')
        if bias_data['g_bias'] > 0.9:
            strategy['specific_actions'].append('Randomize G-channel LSB')
        if bias_data['b_bias'] > 0.9:
            strategy['specific_actions'].append('Randomize B-channel LSB')
    
    if patterns.get('sequential_encoding', {}).get('suspicious'):
        strategy['method'] = 'selective_clean'
        strategy['specific_actions'].append('Break sequential color patterns')
    
    if patterns.get('white_pixel_encoding', {}).get('suspicious'):
        strategy['specific_actions'].append('Target near-white pixels specifically')
        strategy['preserve_quality'] = 0.99  # Higher quality for white pixels
    
    return strategy


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pattern_identifier.py <image_path>")
        sys.exit(1)
    
    detector = AdvancedPatternDetector()
    patterns = detector.analyze_encoding_scheme(sys.argv[1])
    
    print("\n📋 DETAILED PATTERN ANALYSIS:")
    for pattern, result in patterns.items():
        print(f"\n{pattern.upper()}:")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print(f"  Result: {result}")
    
    strategy = create_cleaning_strategy(patterns)
    print("\n🎯 RECOMMENDED CLEANING STRATEGY:")
    for key, value in strategy.items():
        print(f"  {key}: {value}")
