"""
Expert Router - Identifies and routes to appropriate expert personas
Based on problem analysis and codebase characteristics
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class ExpertRecommendation:
    """Recommendation for which expert to use."""
    expert_type: str
    confidence: float
    reasoning: str
    recommended_actions: List[str]
    persona_file: str


class ExpertRouter:
    """Routes problems to appropriate expert personas based on analysis."""

    def __init__(self):
        self.personas_dir = Path(".cursor/personas")
        self.expert_profiles = self._load_expert_profiles()

    def _load_expert_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load expert persona profiles."""
        profiles = {}

        if self.personas_dir.exists():
            for persona_file in self.personas_dir.glob("*.md"):
                expert_type = persona_file.stem
                try:
                    with open(persona_file, 'r') as f:
                        content = f.read()
                        profiles[expert_type] = {
                            'file': str(persona_file),
                            'content': content
                        }
                except Exception as e:
                    print(f"Failed to load persona {persona_file}: {e}")

        return profiles

    def identify_experts(self, problem_description: str, codebase_context: Dict[str, Any] = None) -> List[ExpertRecommendation]:
        """Identify appropriate experts for a given problem."""
        recommendations = []

        # Analyze problem characteristics
        problem_keywords = self._extract_keywords(problem_description)
        problem_type = self._classify_problem_type(problem_description, problem_keywords)

        # Match to expert personas
        for expert_type, profile in self.expert_profiles.items():
            confidence, reasoning = self._calculate_expert_match(
                expert_type, profile, problem_keywords, problem_type, codebase_context
            )

            if confidence > 0.3:  # Minimum confidence threshold
                recommendation = ExpertRecommendation(
                    expert_type=expert_type,
                    confidence=confidence,
                    reasoning=reasoning,
                    recommended_actions=self._get_expert_actions(expert_type, problem_type),
                    persona_file=profile['file']
                )
                recommendations.append(recommendation)

        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return recommendations

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from problem description."""
        # Common technical keywords
        technical_keywords = [
            'encryption', 'decryption', 'cryptography', 'security', 'hash', 'key', 'certificate',
            'image', 'computer vision', 'opencv', 'pixel', 'detection', 'recognition',
            'forensics', 'malware', 'evidence', 'analysis', 'recovery',
            'text', 'ocr', 'pattern', 'watermark', 'steganography',
            'network', 'protocol', 'authentication', 'authorization'
        ]

        text_lower = text.lower()
        found_keywords = []

        for keyword in technical_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _classify_problem_type(self, description: str, keywords: List[str]) -> str:
        """Classify the type of problem based on keywords."""
        desc_lower = description.lower()

        # Cryptography problems
        if any(k in desc_lower for k in ['encryption', 'decryption', 'cryptography', 'key', 'hash', 'certificate']):
            return 'cryptography'

        # Computer vision problems
        if any(k in desc_lower for k in ['image', 'computer vision', 'pixel', 'detection', 'recognition', 'opencv']):
            return 'computer_vision'

        # Digital forensics problems
        if any(k in desc_lower for k in ['forensics', 'malware', 'evidence', 'analysis', 'recovery']):
            return 'digital_forensics'

        # Text processing problems
        if any(k in desc_lower for k in ['text', 'ocr', 'pattern', 'watermark', 'steganography']):
            return 'text_processing'

        # Default classification
        return 'general_analysis'

    def _calculate_expert_match(self, expert_type: str, profile: Dict[str, Any],
                              keywords: List[str], problem_type: str,
                              codebase_context: Dict[str, Any] = None) -> Tuple[float, str]:
        """Calculate how well an expert matches the problem."""

        # Base matching on problem type
        type_match = {
            'cryptography_expert': ['cryptography'],
            'computer_vision_expert': ['computer_vision', 'text_processing'],
            'digital_forensics_expert': ['digital_forensics']
        }

        base_confidence = 0.0
        if expert_type in type_match and problem_type in type_match[expert_type]:
            base_confidence = 0.8

        # Keyword matching
        content = profile['content'].lower()
        keyword_matches = sum(1 for keyword in keywords if keyword in content)
        keyword_confidence = min(0.9, keyword_matches * 0.1)

        # Combine confidences
        total_confidence = min(0.95, base_confidence + keyword_confidence)

        # Generate reasoning
        reasoning = f"Problem classified as '{problem_type}' with {len(keywords)} relevant keywords. "
        reasoning += f"Expert {expert_type} has {keyword_matches} matching keywords."

        return total_confidence, reasoning

    def _get_expert_actions(self, expert_type: str, problem_type: str) -> List[str]:
        """Get recommended actions for an expert."""
        actions = []

        if expert_type == 'cryptography_expert':
            actions.extend([
                "Analyze encryption requirements and security properties",
                "Evaluate cryptographic algorithm selection",
                "Design secure key management systems",
                "Implement proper authentication protocols"
            ])

        elif expert_type == 'computer_vision_expert':
            actions.extend([
                "Analyze image processing requirements",
                "Design computer vision algorithms",
                "Implement feature extraction and pattern recognition",
                "Optimize for real-time performance"
            ])

        elif expert_type == 'digital_forensics_expert':
            actions.extend([
                "Preserve evidence chain of custody",
                "Analyze file system artifacts",
                "Correlate timeline and metadata",
                "Document investigation findings"
            ])

        return actions

    def route_to_expert(self, problem_description: str, codebase_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route a problem to the most appropriate expert."""
        recommendations = self.identify_experts(problem_description, codebase_context)

        if not recommendations:
            return {
                'error': 'No suitable expert found',
                'recommendations': []
            }

        # Get the top recommendation
        top_expert = recommendations[0]

        # Load the expert persona
        persona_content = ""
        if os.path.exists(top_expert.persona_file):
            try:
                with open(top_expert.persona_file, 'r') as f:
                    persona_content = f.read()
            except Exception as e:
                persona_content = f"Error loading persona: {e}"

        return {
            'recommended_expert': top_expert.expert_type,
            'confidence': top_expert.confidence,
            'reasoning': top_expert.reasoning,
            'persona_content': persona_content,
            'recommended_actions': top_expert.recommended_actions,
            'all_recommendations': [
                {
                    'expert': r.expert_type,
                    'confidence': r.confidence,
                    'reasoning': r.reasoning
                }
                for r in recommendations[:3]  # Top 3 alternatives
            ]
        }


def identify_experts_for_problem(problem_description: str, codebase_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to identify experts for a problem."""
    router = ExpertRouter()
    return router.route_to_expert(problem_description, codebase_context)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python expert_router.py \"problem description\"")
        sys.exit(1)

    problem = sys.argv[1]

    print(f"🔍 ANALYZING PROBLEM: {problem}")

    result = identify_experts_for_problem(problem)

    if 'error' in result:
        print(f"❌ {result['error']}")
        sys.exit(1)

    print("\n🎯 RECOMMENDED EXPERT:")
    print(f"  Expert: {result['recommended_expert']}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Reasoning: {result['reasoning']}")

    print("\n💡 RECOMMENDED ACTIONS:")
    for action in result['recommended_actions']:
        print(f"  • {action}")

    print("\n🤖 EXPERT PERSONA:")
    print(result['persona_content'][:500] + "..." if len(result['persona_content']) > 500 else result['persona_content'])
