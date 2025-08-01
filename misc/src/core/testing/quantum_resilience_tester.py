#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quantum Resilience Tester Module for Phoenix DemiGod

This module implements testing mechanisms to evaluate system robustness against
decoherence attacks, quantum noise, and adversarial model perturbations.
"""

import logging
import math
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Callable

import numpy as np
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/quantum_resilience.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("QuantumResilience")

class QuantumResilienceTester:
    """
    Tester for evaluating system resilience against quantum-inspired attacks.
    
    Attributes:
        attack_types (List[str]): Available attack types
        test_duration (int): Default test duration in seconds
        tolerance (float): Tolerance threshold for resilience
        verbose (bool): Whether to print verbose output
    """
    
    def __init__(
        self,
        attack_types: List[str] = None,
        test_duration: int = 60,
        tolerance: float = 0.8,
        verbose: bool = False
    ):
        """
        Initialize the quantum resilience tester.
        
        Args:
            attack_types: Available attack types
            test_duration: Default test duration in seconds
            tolerance: Tolerance threshold for resilience (0-1)
            verbose: Whether to print verbose output
        """
        self.attack_types = attack_types or [
            "decoherence",
            "entanglement_breaking",
            "adversarial_perturbation",
            "quantum_noise",
            "measurement_disruption",
            "phase_instability"
        ]
        
        self.test_duration = test_duration
        self.tolerance = min(1.0, max(0.0, tolerance))  # Clamp to [0, 1]
        self.verbose = verbose
        self.latest_results = {}
        
        logger.info(f"QuantumResilienceTester initialized with {len(self.attack_types)} attack types")
    
    def test_resilience(
        self,
        system_function: Callable,
        attack_type: str = None,
        duration: int = None,
        intensity: float = 0.5,
        repetitions: int = 3
    ) -> Dict:
        """
        Test system resilience against a specific attack type.
        
        Args:
            system_function: Function that represents the system under test
            attack_type: Type of attack to simulate (if None, all types are tested)
            duration: Test duration in seconds (if None, use default)
            intensity: Attack intensity (0-1)
            repetitions: Number of test repetitions
            
        Returns:
            Test results
        """
        if attack_type is not None and attack_type not in self.attack_types:
            raise ValueError(f"Unknown attack type: {attack_type}. Available types: {self.attack_types}")
        
        duration = duration or self.test_duration
        attack_types = [attack_type] if attack_type else self.attack_types
        intensity = min(1.0, max(0.0, intensity))  # Clamp to [0, 1]
        
        results = {}
        
        for attack in attack_types:
            attack_results = []
            
            if self.verbose:
                logger.info(f"Testing resilience against {attack} attack (intensity={intensity})...")
            
            for i in range(repetitions):
                if self.verbose:
                    logger.info(f"  Repetition {i+1}/{repetitions}")
                
                # Create attack function
                attack_function = self._create_attack_function(attack, intensity)
                
                # Measure baseline performance
                baseline_start = time.time()
                baseline_result = system_function()
                baseline_time = time.time() - baseline_start
                
                # Apply attack and measure performance
                attack_start = time.time()
                attacked_result = None
                
                try:
                    # Apply the attack for the specified duration
                    end_time = time.time() + duration
                    attacked_result = attack_function(system_function)
                    while time.time() < end_time:
                        # Continue attacking until duration expires
                        attacked_result = attack_function(system_function)
                except Exception as e:
                    logger.error(f"Attack caused system error: {str(e)}")
                    # Consider system crash as zero resilience
                    attack_results.append(0.0)
                    continue
                
                attack_time = time.time() - attack_start
                
                # Calculate resilience score
                resilience_score = self._calculate_resilience(
                    baseline_result,
                    attacked_result,
                    baseline_time,
                    attack_time
                )
                
                attack_results.append(resilience_score)
            
            # Calculate average resilience
            avg_resilience = sum(attack_results) / len(attack_results) if attack_results else 0.0
            
            results[attack] = {
                "resilience_score": avg_resilience,
                "passed": avg_resilience >= self.tolerance,
                "repetitions": repetitions,
                "intensity": intensity,
                "duration": duration,
                "individual_scores": attack_results,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.verbose:
                status = "PASSED" if results[attack]["passed"] else "FAILED"
                logger.info(f"  Resilience against {attack}: {avg_resilience:.2f} ({status})")
        
        self.latest_results = results
        return results
    
    def _create_attack_function(self, attack_type: str, intensity: float) -> Callable:
        """
        Create a function that simulates a specific attack type.
        
        Args:
            attack_type: Type of attack to simulate
            intensity: Attack intensity (0-1)
            
        Returns:
            Attack function
        """
        if attack_type == "decoherence":
            # Simulate quantum decoherence by adding noise to results
            def decoherence_attack(func):
                result = func()
                
                if isinstance(result, np.ndarray):
                    # Add Gaussian noise proportional to intensity
                    noise = np.random.normal(0, intensity * np.std(result), result.shape)
                    return result + noise
                elif isinstance(result, torch.Tensor):
                    # Add Gaussian noise proportional to intensity
                    noise = torch.randn_like(result) * intensity * torch.std(result)
                    return result + noise
                elif isinstance(result, (int, float)):
                    # Add proportional noise
                    noise = random.gauss(0, abs(result) * intensity * 0.1)
                    return result + noise
                elif isinstance(result, dict):
                    # Recursively add noise to numerical values
                    noisy_result = {}
                    for key, value in result.items():
                        if isinstance(value, (int, float)):
                            noise = random.gauss(0, abs(value) * intensity * 0.1)
                            noisy_result[key] = value + noise
                        else:
                            noisy_result[key] = value
                    return noisy_result
                else:
                    # For other types, return as is
                    return result
            
            return decoherence_attack
        
        elif attack_type == "entanglement_breaking":
            # Simulate breaking quantum entanglement by zeroing out correlations
            def entanglement_breaking_attack(func):
                result = func()
                
                if isinstance(result, np.ndarray) and result.ndim >= 2:
                    # Zero out off-diagonal elements (correlations) with probability proportional to intensity
                    mask = np.random.rand(*result.shape) < intensity
                    zeroed_result = result.copy()
                    if result.ndim == 2:
                        # For matrices, zero out off-diagonal elements
                        np.fill_diagonal(mask, False)  # Don't zero out diagonal
                        zeroed_result[mask] = 0
                    return zeroed_result
                elif isinstance(result, torch.Tensor) and result.dim() >= 2:
                    # Zero out off-diagonal elements (correlations) with probability proportional to intensity
                    mask = torch.rand_like(result) < intensity
                    zeroed_result = result.clone()
                    if result.dim() == 2:
                        # For matrices, zero out off-diagonal elements
                        mask.fill_diagonal_(False)  # Don't zero out diagonal
                        zeroed_result[mask] = 0
                    return zeroed_result
                else:
                    # For other types, return as is
                    return result
            
            return entanglement_breaking_attack
        
        elif attack_type == "adversarial_perturbation":
            # Simulate adversarial perturbations by adding targeted noise
            def adversarial_perturbation_attack(func):
                result = func()
                
                if isinstance(result, np.ndarray):
                    # Create adversarial perturbation in the direction of gradient (simulated)
                    perturbation = np.sign(np.random.randn(*result.shape)) * intensity * np.abs(result)
                    return result + perturbation
                elif isinstance(result, torch.Tensor):
                    # Create adversarial perturbation in the direction of gradient (simulated)
                    perturbation = torch.sign(torch.randn_like(result)) * intensity * torch.abs(result)
                    return result + perturbation
                elif isinstance(result, (int, float)):
                    # Add adversarial noise
                    direction = 1 if random.random() > 0.5 else -1
                    perturbation = direction * abs(result) * intensity * 0.2
                    return result + perturbation
                else:
                    # For other types, return as is
                    return result
            
            return adversarial_perturbation_attack
        
        elif attack_type == "quantum_noise":
            # Simulate quantum noise by adding phase rotations and bit flips
            def quantum_noise_attack(func):
                result = func()
                
                if isinstance(result, np.ndarray):
                    # Apply simulated quantum noise (phase rotations)
                    phase_shifts = np.exp(1j * np.random.uniform(0, intensity * 2 * np.pi, result.shape))
                    noisy_result = result.astype(complex) * phase_shifts
                    
                    # Take real part for output
                    return np.real(noisy_result).astype(result.dtype)
                elif isinstance(result, torch.Tensor):
                    # Apply simulated quantum noise (phase rotations)
                    if result.is_complex():
                        phase_shifts = torch.exp(1j * torch.rand_like(result) * intensity * 2 * torch.pi)
                        return result * phase_shifts
                    else:
                        # Convert to complex, apply noise, then take real part
                        complex_result = torch.complex(result, torch.zeros_like(result))
                        phase_shifts = torch.exp(1j * torch.rand_like(complex_result) * intensity * 2 * torch.pi)
                        noisy_result = complex_result * phase_shifts
                        return torch.real(noisy_result)
                else:
                    # For other types, return as is
                    return result
            
            return quantum_noise_attack
        
        elif attack_type == "measurement_disruption":
            # Simulate disruption of quantum measurements by randomizing results
            def measurement_disruption_attack(func):
                result = func()
                
                # With probability proportional to intensity, replace result with random values
                if random.random() < intensity:
                    if isinstance(result, np.ndarray):
                        return np.random.rand(*result.shape).astype(result.dtype) * np.mean(np.abs(result))
                    elif isinstance(result, torch.Tensor):
                        return torch.rand_like(result) * torch.mean(torch.abs(result))
                    elif isinstance(result, (int, float)):
                        return random.random() * result
                    elif isinstance(result, dict):
                        # Randomize numerical values
                        random_result = {}
                        for key, value in result.items():
                            if isinstance(value, (int, float)):
                                random_result[key] = random.random() * value
                            else:
                                random_result[key] = value
                        return random_result
                
                return result
            
            return measurement_disruption_attack
        
        elif attack_type == "phase_instability":
            # Simulate phase instability in quantum systems
            def phase_instability_attack(func):
                result = func()
                
                # Apply periodic perturbation
                phase = random.uniform(0, 2 * math.pi)
                
                if isinstance(result, np.ndarray):
                    # Apply sinusoidal modulation
                    modulation = 1.0 + intensity * np.sin(phase + np.linspace(0, 10, np.prod(result.shape)).reshape(result.shape))
                    return result * modulation
                elif isinstance(result, torch.Tensor):
                    # Apply sinusoidal modulation
                    t = torch.linspace(0, 10, result.numel(), device=result.device).reshape(result.shape)
                    modulation = 1.0 + intensity * torch.sin(phase + t)
                    return result * modulation
                elif isinstance(result, (int, float)):
                    # Apply sinusoidal modulation
                    modulation = 1.0 + intensity * math.sin(phase)
                    return result * modulation
                else:
                    # For other types, return as is
                    return result
            
            return phase_instability_attack
        
        else:
            # Default: no attack
            return lambda func: func()
    
    def _calculate_resilience(
        self,
        baseline_result,
        attacked_result,
        baseline_time: float,
        attack_time: float
    ) -> float:
        """
        Calculate resilience score based on results and execution times.
        
        Args:
            baseline_result: Result from normal system operation
            attacked_result: Result from system under attack
            baseline_time: Execution time under normal conditions
            attack_time: Execution time under attack
            
        Returns:
            Resilience score (0-1)
        """
        # If attacked_result is None, system failed completely
        if attacked_result is None:
            return 0.0
        
        # If baseline_result and attacked_result are identical, perfect resilience
        if baseline_result == attacked_result:
            return 1.0
        
        # Calculate result similarity score
        similarity = self._calculate_similarity(baseline_result, attacked_result)
        
        # Calculate performance degradation score
        # If attack_time is much larger than baseline_time, performance degraded significantly
        time_ratio = baseline_time / attack_time if attack_time > 0 else 0.0
        performance_score = min(1.0, time_ratio)
        
        # Combine scores (weighted average)
        # Result similarity is more important than performance
        resilience_score = 0.7 * similarity + 0.3 * performance_score
        
        return resilience_score
    
    def _calculate_similarity(self, baseline_result, attacked_result) -> float:
        """
        Calculate similarity between baseline and attacked results.
        
        Args:
            baseline_result: Result from normal system operation
            attacked_result: Result from system under attack
            
        Returns:
            Similarity score (0-1)
        """
        # Handle numpy arrays
        if isinstance(baseline_result, np.ndarray) and isinstance(attacked_result, np.ndarray):
            if baseline_result.shape != attacked_result.shape:
                return 0.0
            
            # Normalize arrays for cosine similarity
            baseline_flat = baseline_result.flatten()
            attacked_flat = attacked_result.flatten()
            
            # Avoid division by zero
            if np.all(baseline_flat == 0) or np.all(attacked_flat == 0):
                return 1.0 if np.array_equal(baseline_flat, attacked_flat) else 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(baseline_flat, attacked_flat) / (np.linalg.norm(baseline_flat) * np.linalg.norm(attacked_flat))
            
            # Convert to range [0, 1]
            return max(0.0, min(1.0, (similarity + 1) / 2))
        
        # Handle PyTorch tensors
        elif isinstance(baseline_result, torch.Tensor) and isinstance(attacked_result, torch.Tensor):
            if baseline_result.shape != attacked_result.shape:
                return 0.0
            
            # Normalize tensors for cosine similarity
            baseline_flat = baseline_result.flatten()
            attacked_flat = attacked_result.flatten()
            
            # Avoid division by zero
            if torch.all(baseline_flat == 0) or torch.all(attacked_flat == 0):
                return 1.0 if torch.equal(baseline_flat, attacked_flat) else 0.0
            
            # Calculate cosine similarity
            similarity = torch.dot(baseline_flat, attacked_flat) / (torch.norm(baseline_flat) * torch.norm(attacked_flat))
            
            # Convert to range [0, 1] and to scalar
            return max(0.0, min(1.0, (similarity.item() + 1) / 2))
        
        # Handle numeric types
        elif isinstance(baseline_result, (int, float)) and isinstance(attacked_result, (int, float)):
            # Calculate relative difference
            max_val = max(abs(baseline_result), abs(attacked_result))
            if max_val == 0:
                return 1.0  # Both are zero, perfect similarity
            
            relative_diff = abs(baseline_result - attacked_result) / max_val
            
            # Convert to similarity score (0-1)
            return max(0.0, 1.0 - relative_diff)
        
        # Handle dictionaries
        elif isinstance(baseline_result, dict) and isinstance(attacked_result, dict):
            # If keys don't match, low similarity
            if set(baseline_result.keys()) != set(attacked_result.keys()):
                return 0.1  # Not zero, but very low
            
            # Calculate similarity for each key
            similarities = []
            
            for key in baseline_result:
                if key in attacked_result:
                    # Recursively calculate similarity for this key
                    key_similarity = self._calculate_similarity(baseline_result[key], attacked_result[key])
                    similarities.append(key_similarity)
            
            # Return average similarity
            return sum(similarities) / len(similarities) if similarities else 0.0
        
        # Handle lists
        elif isinstance(baseline_result, list) and isinstance(attacked_result, list):
            # If lengths don't match, low similarity
            if len(baseline_result) != len(attacked_result):
                return 0.1  # Not zero, but very low
            
            # Calculate similarity for each element
            similarities = []
            
            for i in range(len(baseline_result)):
                if i < len(attacked_result):
                    # Recursively calculate similarity for this element
                    elem_similarity = self._calculate_similarity(baseline_result[i], attacked_result[i])
                    similarities.append(elem_similarity)
            
            # Return average similarity
            return sum(similarities) / len(similarities) if similarities else 0.0
        
        # For other types, use simple equality check
        return 1.0 if baseline_result == attacked_result else 0.0
    
    def get_overall_resilience(self) -> Tuple[float, Dict]:
        """
        Calculate overall system resilience based on latest results.
        
        Returns:
            Tuple of (overall_score, detailed_results)
        """
        if not self.latest_results:
            return 0.0, {}
        
        # Calculate weighted average of resilience scores
        # Weights are based on attack severity (currently all equal)
        weights = {
            "decoherence": 1.0,
            "entanglement_breaking": 1.0,
            "adversarial_perturbation": 1.0,
            "quantum_noise": 1.0,
            "measurement_disruption": 1.0,
            "phase_instability": 1.0
        }
        
        total_score = 0.0
        total_weight = 0.0
        attack_results = {}
        
        for attack_type, result in self.latest_results.items():
            if attack_type in weights:
                weight = weights[attack_type]
                score = result["resilience_score"]
                
                total_score += score * weight
                total_weight += weight
                
                status = "PASSED" if result["passed"] else "FAILED"
                attack_results[attack_type] = {
                    "score": score,
                    "status": status,
                    "weight": weight
                }
        
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        
        detailed_results = {
            "overall_score": overall_score,
            "overall_status": "PASSED" if overall_score >= self.tolerance else "FAILED",
            "tolerance": self.tolerance,
            "attack_results": attack_results,
            "timestamp": datetime.now().isoformat()
        }
        
        return overall_score, detailed_results
    
    def generate_report(self, format_type: str = "text") -> str:
        """
        Generate a report of the resilience testing results.
        
        Args:
            format_type: Report format ("text", "json", "html")
            
        Returns:
            Formatted report
        """
        if not self.latest_results:
            return "No test results available"
        
        overall_score, detailed_results = self.get_overall_resilience()
        
        if format_type == "json":
            import json
            report_data = {
                "overall_resilience": {
                    "score": overall_score,
                    "status": detailed_results["overall_status"],
                    "tolerance": self.tolerance
                },
                "attack_results": self.latest_results,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(report_data, indent=2)
        
        elif format_type == "html":
            # Simple HTML report
            html_parts = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                "<title>Quantum Resilience Test Report</title>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                "h1 { color: #333; }",
                "h2 { color: #666; }",
                ".passed { color: green; }",
                ".failed { color: red; }",
                "table { border-collapse: collapse; width: 100%; }",
                "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "th { background-color: #f2f2f2; }",
                "</style>",
                "</head>",
                "<body>",
                f"<h1>Quantum Resilience Test Report</h1>",
                f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
                
                f"<h2>Overall Resilience: <span class=\"{'passed' if overall_score >= self.tolerance else 'failed'}\">{overall_score:.2f}</span></h2>",
                f"<p>Tolerance Threshold: {self.tolerance:.2f}</p>",
                
                "<h2>Attack Resilience Details</h2>",
                "<table>",
                "<tr><th>Attack Type</th><th>Resilience Score</th><th>Status</th><th>Intensity</th><th>Duration</th></tr>"
            ]
            
            for attack_type, result in self.latest_results.items():
                status_class = "passed" if result["passed"] else "failed"
                html_parts.append(
                    f"<tr>"
                    f"<td>{attack_type}</td>"
                    f"<td>{result['resilience_score']:.2f}</td>"
                    f"<td class=\"{status_class}\">{result['passed'] and 'PASSED' or 'FAILED'}</td>"
                    f"<td>{result['intensity']:.2f}</td>"
                    f"<td>{result['duration']} s</td>"
                    f"</tr>"
                )
            
            html_parts.extend([
                "</table>",
                "</body>",
                "</html>"
            ])
            
            return "\n".join(html_parts)
        
        else:  # text format
            report_parts = [
                "=" * 50,
                "QUANTUM RESILIENCE TEST REPORT",
                "=" * 50,
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                f"OVERALL RESILIENCE SCORE: {overall_score:.2f}",
                f"STATUS: {detailed_results['overall_status']}",
                f"TOLERANCE THRESHOLD: {self.tolerance:.2f}",
                "",
                "ATTACK RESILIENCE DETAILS",
                "-" * 50
            ]
            
            for attack_type, result in self.latest_results.items():
                report_parts.extend([
                    f"Attack Type: {attack_type}",
                    f"  Resilience Score: {result['resilience_score']:.2f}",
                    f"  Status: {result['passed'] and 'PASSED' or 'FAILED'}",
                    f"  Intensity: {result['intensity']:.2f}",
                    f"  Duration: {result['duration']} s",
                    f"  Repetitions: {result['repetitions']}",
                    "-" * 30
                ])
            
            report_parts.append("=" * 50)
            
            return "\n".join(report_parts)


# Example usage
def simple_system_function():
    """Example system function for testing resilience."""
    # Simulate complex computation
    time.sleep(0.1)
    
    # Return random array (simulating quantum state)
    return np.random.rand(10, 10)

if __name__ == "__main__":
    # Create tester
    tester = QuantumResilienceTester(verbose=True)
    
    # Test system resilience
    results = tester.test_resilience(
        system_function=simple_system_function,
        attack_type="quantum_noise",
        intensity=0.3,
        repetitions=2
    )
    
    # Generate report
    report = tester.generate_report()
    print(report)
