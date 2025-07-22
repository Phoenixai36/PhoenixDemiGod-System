#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ethical Governance Module for Phoenix DemiGod

This module provides ethical oversight and governance for AI decision-making,
implementing principled constraints, bias detection, explainability mechanisms,
and auditing capabilities.
"""

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ethical_governance.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EthicalGovernance")

class EthicalPrinciple:
    """
    Represents an ethical principle to be enforced.
    
    Attributes:
        name (str): Name of the principle
        description (str): Description of what the principle entails
        category (str): Category of the principle (e.g., 'fairness', 'safety')
        check_function (Callable): Function to check if a decision adheres to the principle
        priority (int): Priority level of the principle (higher values are more important)
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        check_function: Callable[[Dict], Tuple[bool, str]],
        priority: int = 1
    ):
        """
        Initialize an ethical principle.
        
        Args:
            name: Name of the principle
            description: Description of what the principle entails
            category: Category of the principle (e.g., 'fairness', 'safety')
            check_function: Function to check if a decision adheres to the principle
            priority: Priority level of the principle (higher values are more important)
        """
        self.name = name
        self.description = description
        self.category = category
        self.check_function = check_function
        self.priority = priority
    
    def check(self, decision_context: Dict) -> Tuple[bool, str]:
        """
        Check if a decision adheres to this principle.
        
        Args:
            decision_context: Context information about the decision
            
        Returns:
            Tuple of (passes_check, explanation)
        """
        try:
            return self.check_function(decision_context)
        except Exception as e:
            logger.error(f"Error checking principle {self.name}: {str(e)}")
            return False, f"Error in principle check: {str(e)}"
    
    def to_dict(self) -> Dict:
        """
        Convert the principle to a dictionary representation.
        
        Returns:
            Dictionary representation of the principle
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "priority": self.priority
        }


class BiasDetector:
    """
    Detector for biases in AI responses and decisions.
    
    Attributes:
        bias_patterns (Dict[str, Tuple[str, float]]): Patterns for detecting bias
        sensitivity (float): Sensitivity level for bias detection
        threshold (float): Threshold for flagging bias
        detection_stats (Dict[str, int]): Statistics on detected biases
    """
    
    def __init__(
        self,
        bias_patterns: Dict[str, Tuple[str, float]] = None,
        sensitivity: float = 0.7,
        threshold: float = 0.5
    ):
        """
        Initialize the bias detector.
        
        Args:
            bias_patterns: Dictionary mapping bias types to (regex pattern, severity) tuples
            sensitivity: Sensitivity level for bias detection (0-1)
            threshold: Threshold for flagging bias (0-1)
        """
        self.bias_patterns = bias_patterns or {}
        self.sensitivity = max(0.0, min(1.0, sensitivity))  # Clamp to [0, 1]
        self.threshold = max(0.0, min(1.0, threshold))  # Clamp to [0, 1]
        self.detection_stats = {}
        
        # Load default patterns if none provided
        if not self.bias_patterns:
            self._load_default_patterns()
        
        logger.info(f"BiasDetector initialized with {len(self.bias_patterns)} patterns")
    
    def _load_default_patterns(self) -> None:
        """Load default bias detection patterns."""
        # This is a simplified set of patterns; a real implementation would have more sophisticated patterns
        self.bias_patterns = {
            "gender_bias": (
                r"\b(?:all|every|most)\s+(?:men|women|males|females)\s+(?:are|seem|appear|tend|like|prefer)\b",
                0.7
            ),
            "racial_bias": (
                r"\b(?:all|every|most)\s+(?:black|white|asian|hispanic|latino|middle\s+eastern)\s+(?:people|persons|individuals)\s+(?:are|seem|appear|tend|like|prefer)\b",
                0.8
            ),
            "age_bias": (
                r"\b(?:all|every|most)\s+(?:old|young|elderly|teenage|millennials|boomers)\s+(?:people|persons|individuals)\s+(?:are|seem|appear|tend|like|prefer)\b",
                0.6
            ),
            "religious_bias": (
                r"\b(?:all|every|most)\s+(?:christians|muslims|jews|hindus|buddhists|atheists)\s+(?:are|seem|appear|tend|like|prefer)\b",
                0.8
            ),
            "political_bias": (
                r"\b(?:all|every|most)\s+(?:conservatives|liberals|republicans|democrats|leftists|rightists)\s+(?:are|seem|appear|tend|like|prefer)\b",
                0.7
            ),
            "generalization": (
                r"\b(?:always|never|everyone|nobody|impossible|guaranteed)\b",
                0.5
            )
        }
    
    def is_biased(self, text: str) -> Tuple[bool, Dict]:
        """
        Check if text contains biased content.
        
        Args:
            text: Text to check for bias
            
        Returns:
            Tuple of (is_biased, bias_details)
        """
        if not text:
            return False, {}
        
        bias_details = {}
        total_bias_score = 0.0
        
        for bias_type, (pattern, severity) in self.bias_patterns.items():
            # Find all matches
            matches = re.finditer(pattern, text, re.IGNORECASE)
            match_count = sum(1 for _ in matches)
            
            if match_count > 0:
                # Calculate bias score based on matches and severity
                bias_score = min(match_count * severity * self.sensitivity, 1.0)
                
                if bias_score >= self.threshold:
                    # Track detection statistics
                    if bias_type not in self.detection_stats:
                        self.detection_stats[bias_type] = 0
                    self.detection_stats[bias_type] += 1
                    
                    # Add to details
                    bias_details[bias_type] = {
                        "score": bias_score,
                        "matches": match_count,
                        "severity": severity
                    }
                    
                    total_bias_score += bias_score
        
        # Normalize total bias score to 0-1 range
        if bias_details:
            normalized_score = min(total_bias_score / len(bias_details), 1.0)
            return normalized_score >= self.threshold, {
                "bias_types": bias_details,
                "overall_score": normalized_score
            }
        
        return False, {}
    
    def filter_bias(self, text: str) -> Tuple[str, Dict]:
        """
        Filter biased content from text.
        
        Args:
            text: Text to filter
            
        Returns:
            Tuple of (filtered_text, bias_details)
        """
        is_biased, bias_details = self.is_biased(text)
        
        if not is_biased:
            return text, bias_details
        
        filtered_text = text
        for bias_type, (pattern, _) in self.bias_patterns.items():
            # Replace biased patterns with more neutral language
            filtered_text = re.sub(
                pattern, 
                "some \\2 may \\3", 
                filtered_text, 
                flags=re.IGNORECASE
            )
        
        return filtered_text, bias_details
    
    def get_stats(self) -> Dict:
        """
        Get statistics on detected biases.
        
        Returns:
            Dictionary with detection statistics
        """
        return {
            "total_detections": sum(self.detection_stats.values()),
            "by_type": self.detection_stats
        }


class EthicalGovernance:
    """
    Main ethical governance module for AI systems.
    
    Attributes:
        principles (List[EthicalPrinciple]): Ethical principles to enforce
        bias_detector (BiasDetector): Detector for biased content
        audit_log (List[Dict]): Log of ethical decisions and analyses
        transparency_level (int): Level of explanation detail (1-5)
    """
    
    def __init__(
        self,
        principles: List[EthicalPrinciple] = None,
        bias_detector: BiasDetector = None,
        transparency_level: int = 3
    ):
        """
        Initialize the ethical governance module.
        
        Args:
            principles: List of ethical principles to enforce
            bias_detector: Detector for biased content
            transparency_level: Level of explanation detail (1-5)
        """
        self.principles = principles or []
        self.bias_detector = bias_detector or BiasDetector()
        self.transparency_level = max(1, min(5, transparency_level))
        self.audit_log = []
        
        # Load default principles if none provided
        if not self.principles:
            self._load_default_principles()
        
        logger.info(f"EthicalGovernance initialized with {len(self.principles)} principles")
    
    def _load_default_principles(self) -> None:
        """Load default ethical principles."""
        self.principles = [
            EthicalPrinciple(
                name="Beneficence",
                description="AI systems should act to benefit users and society",
                category="core",
                check_function=self._check_beneficence,
                priority=5
            ),
            EthicalPrinciple(
                name="Non-maleficence",
                description="AI systems should not cause harm",
                category="core",
                check_function=self._check_non_maleficence,
                priority=5
            ),
            EthicalPrinciple(
                name="Fairness",
                description="AI systems should treat all individuals fairly",
                category="social",
                check_function=self._check_fairness,
                priority=4
            ),
            EthicalPrinciple(
                name="Transparency",
                description="AI decisions should be explainable and transparent",
                category="governance",
                check_function=self._check_transparency,
                priority=4
            ),
            EthicalPrinciple(
                name="Privacy",
                description="AI systems should respect user privacy",
                category="rights",
                check_function=self._check_privacy,
                priority=4
            ),
            EthicalPrinciple(
                name="Autonomy",
                description="AI systems should respect user autonomy and choice",
                category="rights",
                check_function=self._check_autonomy,
                priority=3
            ),
            EthicalPrinciple(
                name="Accountability",
                description="AI systems should have clear accountability mechanisms",
                category="governance",
                check_function=self._check_accountability,
                priority=3
            )
        ]
    
    def _check_beneficence(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of beneficence."""
        # This is a simplified check; a real implementation would be more sophisticated
        if "purpose" not in context or not context["purpose"]:
            return False, "No clear purpose or benefit identified"
        
        # Check if the purpose is beneficial
        beneficial_keywords = ["help", "assist", "support", "improve", "enhance", "benefit"]
        purpose = context["purpose"].lower()
        
        if any(keyword in purpose for keyword in beneficial_keywords):
            return True, "Decision has a clear beneficial purpose"
        
        return False, "Decision does not demonstrate clear benefit to users or society"
    
    def _check_non_maleficence(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of non-maleficence."""
        # Check for harmful content
        if "content" in context and context["content"]:
            is_biased, bias_details = self.bias_detector.is_biased(context["content"])
            if is_biased:
                return False, f"Content contains potentially harmful bias: {bias_details}"
        
        # Check for harmful actions
        harmful_actions = ["delete", "remove", "block", "restrict"]
        if "action" in context and any(action in context["action"].lower() for action in harmful_actions):
            if "justification" not in context or not context["justification"]:
                return False, "Potentially harmful action without clear justification"
        
        return True, "No potential harm identified"
    
    def _check_fairness(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of fairness."""
        # Check for potentially unfair treatment
        protected_attributes = ["gender", "race", "age", "religion", "disability"]
        
        for attr in protected_attributes:
            if attr in context and context[attr] is not None:
                # If decision depends on a protected attribute, check for justification
                if "fairness_justification" not in context or not context["fairness_justification"]:
                    return False, f"Decision depends on protected attribute ({attr}) without fairness justification"
        
        return True, "No fairness concerns identified"
    
    def _check_transparency(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of transparency."""
        # Check if explanation is provided
        if "explanation" not in context or not context["explanation"]:
            return False, "No explanation provided for decision"
        
        # Check explanation quality based on transparency level
        explanation = context["explanation"]
        if self.transparency_level >= 4:
            # High transparency requires detailed explanations
            min_length = 100
            if len(explanation) < min_length:
                return False, f"Explanation too brief for high transparency level (min {min_length} chars)"
        
        return True, "Decision includes adequate explanation"
    
    def _check_privacy(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of privacy."""
        # Check for personal data usage
        personal_data_types = ["name", "email", "address", "phone", "health_info", "financial_info"]
        used_personal_data = [data_type for data_type in personal_data_types if data_type in context]
        
        if used_personal_data:
            # If using personal data, check for consent
            if "consent" not in context or not context["consent"]:
                return False, f"Using personal data ({', '.join(used_personal_data)}) without explicit consent"
        
        return True, "No privacy concerns identified"
    
    def _check_autonomy(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of autonomy."""
        # Check if user choice is respected
        if "override_user_choice" in context and context["override_user_choice"]:
            if "override_justification" not in context or not context["override_justification"]:
                return False, "Overriding user choice without clear justification"
        
        return True, "User autonomy respected"
    
    def _check_accountability(self, context: Dict) -> Tuple[bool, str]:
        """Check if a decision adheres to the principle of accountability."""
        # Check for decision tracking
        if "decision_id" not in context or not context["decision_id"]:
            return False, "Decision lacks unique identifier for tracking"
        
        # Check for responsible entity
        if "responsible_entity" not in context or not context["responsible_entity"]:
            return False, "No clear responsible entity identified for this decision"
        
        return True, "Decision has proper accountability mechanisms"
    
    def evaluate_decision(self, decision_context: Dict) -> Dict:
        """
        Evaluate a decision against ethical principles.
        
        Args:
            decision_context: Context information about the decision
            
        Returns:
            Evaluation results
        """
        if not decision_context:
            return {
                "status": "error",
                "message": "No decision context provided",
                "timestamp": datetime.now().isoformat()
            }
        
        # Add decision ID if not present
        if "decision_id" not in decision_context:
            decision_context["decision_id"] = f"decision_{uuid.uuid4()}"
        
        # Check decision against all principles
        results = []
        overall_compliant = True
        
        # Sort principles by priority (highest first)
        sorted_principles = sorted(self.principles, key=lambda p: p.priority, reverse=True)
        
        for principle in sorted_principles:
            compliant, explanation = principle.check(decision_context)
            
            result = {
                "principle": principle.name,
                "category": principle.category,
                "compliant": compliant,
                "explanation": explanation,
                "priority": principle.priority
            }
            
            results.append(result)
            
            # If a high-priority principle (4-5) is violated, mark as non-compliant
            if not compliant and principle.priority >= 4:
                overall_compliant = False
        
        # Check for bias if content is present
        bias_analysis = None
        if "content" in decision_context and decision_context["content"]:
            is_biased, bias_details = self.bias_detector.is_biased(decision_context["content"])
            
            bias_analysis = {
                "is_biased": is_biased,
                "details": bias_details
            }
            
            # Bias is considered a violation of fairness and non-maleficence
            if is_biased:
                overall_compliant = False
        
        # Prepare evaluation result
        evaluation = {
            "decision_id": decision_context["decision_id"],
            "timestamp": datetime.now().isoformat(),
            "overall_compliant": overall_compliant,
            "principle_evaluations": results,
            "bias_analysis": bias_analysis
        }
        
        # Add to audit log
        self.audit_log.append(evaluation)
        
        return evaluation
    
    def get_explanation(self, evaluation: Dict) -> str:
        """
        Generate a human-readable explanation of an ethical evaluation.
        
        Args:
            evaluation: The evaluation result
            
        Returns:
            Human-readable explanation
        """
        if not evaluation or "principle_evaluations" not in evaluation:
            return "No evaluation provided"
        
        # Adjust explanation detail based on transparency level
        if self.transparency_level <= 2:
            # Simple explanation
            if evaluation["overall_compliant"]:
                return "Decision complies with ethical principles"
            else:
                violations = [p["principle"] for p in evaluation["principle_evaluations"] if not p["compliant"]]
                return f"Decision violates ethical principles: {', '.join(violations)}"
        
        elif self.transparency_level <= 4:
            # Moderate explanation
            lines = ["Ethical Evaluation:"]
            
            if evaluation["overall_compliant"]:
                lines.append("✓ Decision complies with all high-priority ethical principles")
            else:
                lines.append("✗ Decision violates one or more high-priority ethical principles")
            
            for eval_item in evaluation["principle_evaluations"]:
                marker = "✓" if eval_item["compliant"] else "✗"
                lines.append(f"{marker} {eval_item['principle']}: {eval_item['explanation']}")
            
            if evaluation.get("bias_analysis", {}).get("is_biased", False):
                lines.append(f"✗ Bias detected: {evaluation['bias_analysis']['details']['overall_score']:.2f} score")
            
            return "\n".join(lines)
        
        else:
            # Detailed explanation
            lines = ["Detailed Ethical Evaluation:"]
            
            if evaluation["overall_compliant"]:
                lines.append("✓ Decision COMPLIES with all high-priority ethical principles")
            else:
                lines.append("✗ Decision VIOLATES one or more high-priority ethical principles")
            
            lines.append("\nPrinciple Evaluations:")
            for eval_item in sorted(evaluation["principle_evaluations"], key=lambda x: x["priority"], reverse=True):
                marker = "✓" if eval_item["compliant"] else "✗"
                priority_stars = "★" * eval_item["priority"]
                lines.append(f"{marker} {eval_item['principle']} ({priority_stars})")
                lines.append(f"   Category: {eval_item['category']}")
                lines.append(f"   {eval_item['explanation']}")
                lines.append("")
            
            if evaluation.get("bias_analysis"):
                lines.append("Bias Analysis:")
                bias_analysis = evaluation["bias_analysis"]
                if bias_analysis["is_biased"]:
                    lines.append(f"✗ Bias detected with overall score: {bias_analysis['details']['overall_score']:.2f}")
                    lines.append("  Detected bias types:")
                    for bias_type, details in bias_analysis["details"]["bias_types"].items():
                        lines.append(f"  - {bias_type}: score {details['score']:.2f}, {details['matches']} matches")
                else:
                    lines.append("✓ No significant bias detected")
            
            lines.append(f"\nDecision ID: {evaluation['decision_id']}")
            lines.append(f"Timestamp: {evaluation['timestamp']}")
            
            return "\n".join(lines)
    
    def get_audit_log(self, filters: Dict = None) -> List[Dict]:
        """
        Get filtered audit log entries.
        
        Args:
            filters: Filters to apply (e.g., {"compliant": False})
            
        Returns:
            Filtered audit log entries
        """
        if not filters:
            return self.audit_log
        
        filtered_log = self.audit_log
        
        if "compliant" in filters:
            filtered_log = [log for log in filtered_log if log["overall_compliant"] == filters["compliant"]]
        
        if "principle" in filters:
            filtered_log = [
                log for log in filtered_log
                if any(eval_item["principle"] == filters["principle"] for eval_item in log["principle_evaluations"])
            ]
        
        if "date_from" in filters:
            date_from = datetime.fromisoformat(filters["date_from"])
            filtered_log = [
                log for log in filtered_log
                if datetime.fromisoformat(log["timestamp"]) >= date_from
            ]
        
        if "date_to" in filters:
            date_to = datetime.fromisoformat(filters["date_to"])
            filtered_log = [
                log for log in filtered_log
                if datetime.fromisoformat(log["timestamp"]) <= date_to
            ]
        
        return filtered_log


# Example usage
if __name__ == "__main__":
    # Create ethical governance system
    governance = EthicalGovernance(transparency_level=5)
    
    # Evaluate a decision
    decision_context = {
        "action": "recommend_content",
        "purpose": "help user find relevant information",
        "content": "Most women prefer emotional support over practical solutions.",
        "explanation": "The recommendation is based on user's previous interactions and content preferences.",
        "responsible_entity": "content_recommendation_system"
    }
    
    evaluation = governance.evaluate_decision(decision_context)
    explanation = governance.get_explanation(evaluation)
    
    print(explanation)
