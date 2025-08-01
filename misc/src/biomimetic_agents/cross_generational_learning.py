"""
Cross-Generational Learning System

This module implements the learning mechanisms that allow biomimetic agents
to inherit knowledge and skills from previous generations, enabling
cumulative intelligence evolution.
"""

import asyncio
import hashlib
import json
import logging
import pickle
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .agent_system import AgentMemory, BiomimeticAgent
from .rubik_genome import Archetype, GeneticBase, RUBIKGenome

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeFragment:
    """A piece of knowledge that can be inherited across generations."""

    fragment_id: str
    knowledge_type: str  # 'skill', 'pattern', 'strategy', 'fact'
    content: Dict[str, Any]
    source_agent_id: str
    source_generation: int
    effectiveness_score: float
    usage_count: int
    creation_time: datetime
    last_used: datetime
    archetype_affinity: Dict[
        str, float
    ]  # How well this knowledge works for each archetype
    genetic_requirements: Dict[
        str, float
    ]  # Required gene expressions for effectiveness


@dataclass
class LearningExperience:
    """A learning experience that can be shared across generations."""

    experience_id: str
    task_type: str
    context: Dict[str, Any]
    actions_taken: List[Dict[str, Any]]
    outcome: Dict[str, Any]
    lessons_learned: List[str]
    effectiveness_metrics: Dict[str, float]
    agent_state: Dict[str, Any]  # Genetic and mood state during experience
    timestamp: datetime


class KnowledgeBase:
    """
    Centralized knowledge repository for cross-generational learning.

    This system stores and manages knowledge fragments and experiences
    that can be inherited by new generations of agents.
    """

    def __init__(self, max_fragments: int = 10000):
        self.max_fragments = max_fragments
        self.knowledge_fragments: Dict[str, KnowledgeFragment] = {}
        self.learning_experiences: Dict[str, LearningExperience] = {}
        self.archetype_knowledge: Dict[Archetype, List[str]] = {
            archetype: [] for archetype in Archetype
        }
        self.knowledge_networks: Dict[
            str, List[str]
        ] = {}  # Related knowledge fragments

        # Performance tracking
        self.inheritance_success_rates: Dict[str, float] = {}
        self.knowledge_evolution_history: List[Dict[str, Any]] = []

        logger.info(
            f"Initialized KnowledgeBase with capacity for {max_fragments} fragments"
        )

    def add_knowledge_fragment(self, fragment: KnowledgeFragment):
        """Add a new knowledge fragment to the base."""
        self.knowledge_fragments[fragment.fragment_id] = fragment

        # Add to archetype-specific knowledge
        best_archetype = max(fragment.archetype_affinity.items(), key=lambda x: x[1])
        if best_archetype[1] > 0.5:  # Minimum affinity threshold
            archetype = Archetype(best_archetype[0])
            if fragment.fragment_id not in self.archetype_knowledge[archetype]:
                self.archetype_knowledge[archetype].append(fragment.fragment_id)

        # Maintain size limit
        if len(self.knowledge_fragments) > self.max_fragments:
            self._prune_knowledge_base()

        logger.debug(f"Added knowledge fragment: {fragment.fragment_id}")

    def add_learning_experience(self, experience: LearningExperience):
        """Add a learning experience to the base."""
        self.learning_experiences[experience.experience_id] = experience

        # Extract knowledge fragments from the experience
        self._extract_knowledge_from_experience(experience)

        logger.debug(f"Added learning experience: {experience.experience_id}")

    def _extract_knowledge_from_experience(self, experience: LearningExperience):
        """Extract reusable knowledge fragments from a learning experience."""
        # Extract successful strategies
        if experience.effectiveness_metrics.get("success", False):
            for i, action in enumerate(experience.actions_taken):
                if action.get("success", False):
                    fragment_id = f"strategy_{experience.experience_id}_{i}"

                    fragment = KnowledgeFragment(
                        fragment_id=fragment_id,
                        knowledge_type="strategy",
                        content={
                            "task_type": experience.task_type,
                            "context_pattern": self._extract_context_pattern(
                                experience.context
                            ),
                            "action": action,
                            "expected_outcome": action.get("result", {}),
                        },
                        source_agent_id=experience.agent_state.get(
                            "agent_id", "unknown"
                        ),
                        source_generation=experience.agent_state.get("generation", 0),
                        effectiveness_score=action.get("effectiveness", 0.5),
                        usage_count=0,
                        creation_time=experience.timestamp,
                        last_used=experience.timestamp,
                        archetype_affinity=self._calculate_archetype_affinity(
                            experience.agent_state
                        ),
                        genetic_requirements=self._extract_genetic_requirements(
                            experience.agent_state
                        ),
                    )

                    self.add_knowledge_fragment(fragment)

        # Extract patterns from context
        context_patterns = self._identify_context_patterns(experience)
        for pattern in context_patterns:
            fragment_id = (
                f"pattern_{hashlib.md5(str(pattern).encode()).hexdigest()[:8]}"
            )

            if fragment_id not in self.knowledge_fragments:
                fragment = KnowledgeFragment(
                    fragment_id=fragment_id,
                    knowledge_type="pattern",
                    content=pattern,
                    source_agent_id=experience.agent_state.get("agent_id", "unknown"),
                    source_generation=experience.agent_state.get("generation", 0),
                    effectiveness_score=experience.effectiveness_metrics.get(
                        "pattern_recognition", 0.5
                    ),
                    usage_count=0,
                    creation_time=experience.timestamp,
                    last_used=experience.timestamp,
                    archetype_affinity=self._calculate_archetype_affinity(
                        experience.agent_state
                    ),
                    genetic_requirements=self._extract_genetic_requirements(
                        experience.agent_state
                    ),
                )

                self.add_knowledge_fragment(fragment)

    def _extract_context_pattern(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract generalizable patterns from context."""
        pattern = {}

        # Extract numerical ranges
        for key, value in context.items():
            if isinstance(value, (int, float)):
                pattern[f"{key}_range"] = self._categorize_numerical_value(value)
            elif isinstance(value, str):
                pattern[f"{key}_category"] = self._categorize_string_value(value)
            elif isinstance(value, bool):
                pattern[key] = value

        return pattern

    def _categorize_numerical_value(self, value: float) -> str:
        """Categorize numerical values into ranges."""
        if value < 0.2:
            return "very_low"
        elif value < 0.4:
            return "low"
        elif value < 0.6:
            return "medium"
        elif value < 0.8:
            return "high"
        else:
            return "very_high"

    def _categorize_string_value(self, value: str) -> str:
        """Categorize string values."""
        # Simple categorization - could be more sophisticated
        if len(value) < 10:
            return "short_text"
        elif len(value) < 100:
            return "medium_text"
        else:
            return "long_text"

    def _identify_context_patterns(
        self, experience: LearningExperience
    ) -> List[Dict[str, Any]]:
        """Identify reusable patterns in the experience context."""
        patterns = []

        # Task type patterns
        if experience.task_type:
            patterns.append(
                {
                    "pattern_type": "task_type",
                    "task_category": experience.task_type,
                    "success_indicators": experience.effectiveness_metrics,
                }
            )

        # Environmental patterns
        if "environmental_factors" in experience.context:
            env_factors = experience.context["environmental_factors"]
            patterns.append(
                {
                    "pattern_type": "environmental",
                    "factors": env_factors,
                    "outcome_correlation": experience.effectiveness_metrics,
                }
            )

        return patterns

    def _calculate_archetype_affinity(
        self, agent_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate how well knowledge applies to each archetype."""
        agent_archetype = agent_state.get("archetype", "explorer")

        # Base affinity - highest for source archetype
        affinity = {archetype.value: 0.2 for archetype in Archetype}
        affinity[agent_archetype] = 0.8

        # Adjust based on genetic similarity requirements
        genetic_profile = agent_state.get("genetic_profile", {})

        # Cross-archetype applicability based on genetic overlap
        for archetype in Archetype:
            if archetype.value != agent_archetype:
                # Calculate genetic compatibility
                compatibility = self._calculate_genetic_compatibility(
                    genetic_profile, archetype
                )
                affinity[archetype.value] = max(
                    affinity[archetype.value], compatibility * 0.6
                )

        return affinity

    def _calculate_genetic_compatibility(
        self, genetic_profile: Dict[str, Any], target_archetype: Archetype
    ) -> float:
        """Calculate genetic compatibility with target archetype."""
        # Simplified compatibility calculation
        # In practice, this would analyze genetic base expressions
        base_compatibility = 0.3

        # Archetype-specific genetic requirements
        archetype_genes = {
            Archetype.EXPLORER: ["CURIOSITY", "ADAPTABILITY", "LEARNING"],
            Archetype.GUARDIAN: ["CAUTION", "ROBUSTNESS", "PERSISTENCE"],
            Archetype.CREATOR: ["CREATIVITY", "REASONING", "PRECISION"],
            Archetype.DESTROYER: ["AGGRESSION", "EFFICIENCY", "FOCUS"],
        }

        required_genes = archetype_genes.get(target_archetype, [])
        gene_match_score = 0.0

        for gene in required_genes:
            if gene.lower() in genetic_profile:
                gene_match_score += genetic_profile[gene.lower()]

        if required_genes:
            gene_match_score /= len(required_genes)

        return base_compatibility + (gene_match_score * 0.4)

    def _extract_genetic_requirements(
        self, agent_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract genetic requirements for knowledge effectiveness."""
        genetic_profile = agent_state.get("genetic_profile", {})

        # Identify key genetic traits that contributed to success
        requirements = {}

        for gene_name, expression_level in genetic_profile.items():
            if expression_level > 1.0:  # Above average expression
                requirements[gene_name] = (
                    expression_level * 0.8
                )  # Require 80% of original

        return requirements

    def _prune_knowledge_base(self):
        """Remove least useful knowledge fragments to maintain size limit."""
        # Sort fragments by utility score (combination of effectiveness and usage)
        fragments = list(self.knowledge_fragments.values())
        fragments.sort(
            key=lambda f: f.effectiveness_score * (1 + f.usage_count), reverse=True
        )

        # Keep top fragments
        keep_count = int(self.max_fragments * 0.9)  # Keep 90% of capacity
        fragments_to_keep = fragments[:keep_count]

        # Update knowledge base
        self.knowledge_fragments = {f.fragment_id: f for f in fragments_to_keep}

        # Update archetype knowledge lists
        for archetype in Archetype:
            self.archetype_knowledge[archetype] = [
                fid
                for fid in self.archetype_knowledge[archetype]
                if fid in self.knowledge_fragments
            ]

        logger.info(f"Pruned knowledge base: kept {len(fragments_to_keep)} fragments")

    def get_relevant_knowledge(
        self, agent: BiomimeticAgent, task_type: str, context: Dict[str, Any]
    ) -> List[KnowledgeFragment]:
        """Get knowledge fragments relevant to an agent and task."""
        relevant_fragments = []

        # Get archetype-specific knowledge
        archetype_fragments = [
            self.knowledge_fragments[fid]
            for fid in self.archetype_knowledge[agent.archetype]
            if fid in self.knowledge_fragments
        ]

        # Filter by task type and genetic compatibility
        for fragment in archetype_fragments:
            # Check task type match
            if fragment.content.get("task_type") == task_type:
                # Check genetic requirements
                if self._meets_genetic_requirements(agent, fragment):
                    # Check context similarity
                    context_similarity = self._calculate_context_similarity(
                        context, fragment.content.get("context_pattern", {})
                    )

                    if context_similarity > 0.3:  # Minimum similarity threshold
                        relevant_fragments.append(fragment)

        # Sort by relevance score
        relevant_fragments.sort(
            key=lambda f: f.effectiveness_score
            * f.archetype_affinity.get(agent.archetype.value, 0.0),
            reverse=True,
        )

        return relevant_fragments[:10]  # Return top 10 most relevant

    def _meets_genetic_requirements(
        self, agent: BiomimeticAgent, fragment: KnowledgeFragment
    ) -> bool:
        """Check if agent meets genetic requirements for knowledge fragment."""
        for gene_name, required_level in fragment.genetic_requirements.items():
            try:
                gene_base = GeneticBase[gene_name.upper()]
                agent_expression = agent.genome.get_effective_expression(gene_base)

                if agent_expression < required_level:
                    return False
            except (KeyError, AttributeError):
                # Gene not found or invalid - skip requirement
                continue

        return True

    def _calculate_context_similarity(
        self, current_context: Dict[str, Any], pattern_context: Dict[str, Any]
    ) -> float:
        """Calculate similarity between current context and pattern context."""
        if not pattern_context:
            return 0.0

        matches = 0
        total_patterns = len(pattern_context)

        for key, pattern_value in pattern_context.items():
            if key in current_context:
                current_value = current_context[key]

                # Handle different value types
                if isinstance(pattern_value, str) and isinstance(
                    current_value, (int, float)
                ):
                    # Compare categorized numerical value
                    if pattern_value == self._categorize_numerical_value(current_value):
                        matches += 1
                elif pattern_value == current_value:
                    matches += 1
                elif isinstance(pattern_value, (int, float)) and isinstance(
                    current_value, (int, float)
                ):
                    # Numerical similarity
                    if abs(pattern_value - current_value) < 0.2:
                        matches += 1

        return matches / total_patterns if total_patterns > 0 else 0.0

    def update_fragment_usage(self, fragment_id: str, effectiveness: float):
        """Update usage statistics for a knowledge fragment."""
        if fragment_id in self.knowledge_fragments:
            fragment = self.knowledge_fragments[fragment_id]
            fragment.usage_count += 1
            fragment.last_used = datetime.now()

            # Update effectiveness score (running average)
            current_effectiveness = fragment.effectiveness_score
            fragment.effectiveness_score = (
                current_effectiveness * (fragment.usage_count - 1) + effectiveness
            ) / fragment.usage_count

            logger.debug(
                f"Updated fragment {fragment_id}: "
                f"usage={fragment.usage_count}, "
                f"effectiveness={fragment.effectiveness_score:.3f}"
            )


class CrossGenerationalLearningSystem:
    """
    Manages cross-generational learning for biomimetic agents.

    This system enables agents to inherit knowledge and skills from
    previous generations, creating cumulative intelligence evolution.
    """

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.inheritance_strategies: Dict[str, Callable] = {
            "direct_inheritance": self._direct_inheritance,
            "selective_inheritance": self._selective_inheritance,
            "adaptive_inheritance": self._adaptive_inheritance,
            "cross_archetype_inheritance": self._cross_archetype_inheritance,
        }

        # Learning parameters
        self.inheritance_rate = 0.7  # Probability of inheriting knowledge
        self.adaptation_rate = 0.3  # Rate of knowledge adaptation
        self.forgetting_rate = 0.1  # Rate of knowledge decay

        logger.info("Initialized Cross-Generational Learning System")

    async def inherit_knowledge(
        self, agent: BiomimeticAgent, strategy: str = "selective_inheritance"
    ) -> Dict[str, Any]:
        """
        Transfer knowledge from previous generations to a new agent.

        Args:
            agent: The agent to receive inherited knowledge
            strategy: Inheritance strategy to use

        Returns:
            Dictionary with inheritance results
        """
        if strategy not in self.inheritance_strategies:
            logger.error(f"Unknown inheritance strategy: {strategy}")
            return {"success": False, "error": "Unknown strategy"}

        try:
            inheritance_func = self.inheritance_strategies[strategy]
            result = await inheritance_func(agent)

            logger.info(
                f"Knowledge inheritance completed for {agent.agent_id}: "
                f"{result.get('fragments_inherited', 0)} fragments inherited"
            )

            return result

        except Exception as e:
            logger.error(f"Knowledge inheritance failed for {agent.agent_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _direct_inheritance(self, agent: BiomimeticAgent) -> Dict[str, Any]:
        """Direct inheritance from same archetype ancestors."""
        archetype_fragments = self.knowledge_base.archetype_knowledge[agent.archetype]
        inherited_count = 0

        for fragment_id in archetype_fragments:
            if fragment_id in self.knowledge_base.knowledge_fragments:
                fragment = self.knowledge_base.knowledge_fragments[fragment_id]

                # Check if agent meets genetic requirements
                if self.knowledge_base._meets_genetic_requirements(agent, fragment):
                    # Inherit with probability based on effectiveness
                    if (
                        np.random.random()
                        < fragment.effectiveness_score * self.inheritance_rate
                    ):
                        await self._transfer_knowledge_to_agent(agent, fragment)
                        inherited_count += 1

        return {
            "success": True,
            "strategy": "direct_inheritance",
            "fragments_inherited": inherited_count,
            "total_available": len(archetype_fragments),
        }

    async def _selective_inheritance(self, agent: BiomimeticAgent) -> Dict[str, Any]:
        """Selective inheritance based on genetic compatibility and effectiveness."""
        all_fragments = list(self.knowledge_base.knowledge_fragments.values())
        inherited_count = 0

        # Sort fragments by compatibility and effectiveness
        compatible_fragments = []

        for fragment in all_fragments:
            if self.knowledge_base._meets_genetic_requirements(agent, fragment):
                archetype_affinity = fragment.archetype_affinity.get(
                    agent.archetype.value, 0.0
                )
                compatibility_score = archetype_affinity * fragment.effectiveness_score

                if compatibility_score > 0.3:  # Minimum threshold
                    compatible_fragments.append((fragment, compatibility_score))

        # Sort by compatibility score
        compatible_fragments.sort(key=lambda x: x[1], reverse=True)

        # Inherit top fragments
        max_inheritance = min(20, len(compatible_fragments))  # Limit inheritance

        for fragment, score in compatible_fragments[:max_inheritance]:
            if np.random.random() < score * self.inheritance_rate:
                await self._transfer_knowledge_to_agent(agent, fragment)
                inherited_count += 1

        return {
            "success": True,
            "strategy": "selective_inheritance",
            "fragments_inherited": inherited_count,
            "total_compatible": len(compatible_fragments),
        }

    async def _adaptive_inheritance(self, agent: BiomimeticAgent) -> Dict[str, Any]:
        """Adaptive inheritance that modifies knowledge based on agent's genetics."""
        base_result = await self._selective_inheritance(agent)
        adapted_count = 0

        # Adapt inherited knowledge to agent's specific genetic profile
        for memory_type in ["semantic", "procedural"]:
            memory_dict = getattr(agent.memory, memory_type)

            for key, knowledge in list(memory_dict.items()):
                if isinstance(knowledge, dict) and "inherited" in knowledge:
                    # Adapt knowledge based on agent's genetic strengths
                    adapted_knowledge = await self._adapt_knowledge_to_genetics(
                        agent, knowledge
                    )

                    if adapted_knowledge != knowledge:
                        memory_dict[key] = adapted_knowledge
                        adapted_count += 1

        base_result["adaptations_made"] = adapted_count
        base_result["strategy"] = "adaptive_inheritance"

        return base_result

    async def _cross_archetype_inheritance(
        self, agent: BiomimeticAgent
    ) -> Dict[str, Any]:
        """Cross-archetype inheritance for hybrid capabilities."""
        inherited_count = 0
        cross_archetype_count = 0

        # Inherit from own archetype first
        own_result = await self._direct_inheritance(agent)
        inherited_count += own_result["fragments_inherited"]

        # Then selectively inherit from other archetypes
        for other_archetype in Archetype:
            if other_archetype == agent.archetype:
                continue

            other_fragments = self.knowledge_base.archetype_knowledge[other_archetype]

            for fragment_id in other_fragments[:5]:  # Limit cross-archetype inheritance
                if fragment_id in self.knowledge_base.knowledge_fragments:
                    fragment = self.knowledge_base.knowledge_fragments[fragment_id]

                    # Lower threshold for cross-archetype inheritance
                    if (
                        fragment.effectiveness_score > 0.7
                        and self.knowledge_base._meets_genetic_requirements(
                            agent, fragment
                        )
                    ):
                        if np.random.random() < 0.3:  # Lower probability
                            await self._transfer_knowledge_to_agent(
                                agent, fragment, cross_archetype=True
                            )
                            inherited_count += 1
                            cross_archetype_count += 1

        return {
            "success": True,
            "strategy": "cross_archetype_inheritance",
            "fragments_inherited": inherited_count,
            "cross_archetype_inherited": cross_archetype_count,
        }

    async def _transfer_knowledge_to_agent(
        self,
        agent: BiomimeticAgent,
        fragment: KnowledgeFragment,
        cross_archetype: bool = False,
    ):
        """Transfer a knowledge fragment to an agent's memory."""
        knowledge_content = fragment.content.copy()
        knowledge_content["inherited"] = True
        knowledge_content["source_generation"] = fragment.source_generation
        knowledge_content["inheritance_time"] = datetime.now().isoformat()
        knowledge_content["cross_archetype"] = cross_archetype

        # Determine where to store the knowledge
        if fragment.knowledge_type == "skill":
            agent.memory.procedural[fragment.fragment_id] = knowledge_content
        elif fragment.knowledge_type == "pattern":
            agent.memory.semantic[f"pattern_{fragment.fragment_id}"] = knowledge_content
        elif fragment.knowledge_type == "strategy":
            agent.memory.procedural[f"strategy_{fragment.fragment_id}"] = (
                knowledge_content
            )
        elif fragment.knowledge_type == "fact":
            agent.memory.semantic[fragment.fragment_id] = knowledge_content

        logger.debug(
            f"Transferred {fragment.knowledge_type} knowledge "
            f"{fragment.fragment_id} to agent {agent.agent_id}"
        )

    async def _adapt_knowledge_to_genetics(
        self, agent: BiomimeticAgent, knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt inherited knowledge to agent's specific genetic profile."""
        adapted_knowledge = knowledge.copy()

        # Modify effectiveness based on genetic compatibility
        genetic_strengths = {}
        for base in GeneticBase:
            expression = agent.genome.get_effective_expression(base)
            if expression > 1.2:  # Above average
                genetic_strengths[base.name.lower()] = expression

        # Enhance knowledge areas that align with genetic strengths
        if "effectiveness_modifiers" not in adapted_knowledge:
            adapted_knowledge["effectiveness_modifiers"] = {}

        for strength, level in genetic_strengths.items():
            if strength in knowledge.get("content", {}):
                modifier = min(1.5, 1.0 + (level - 1.0) * 0.3)
                adapted_knowledge["effectiveness_modifiers"][strength] = modifier

        adapted_knowledge["genetic_adaptation"] = True
        adapted_knowledge["adaptation_time"] = datetime.now().isoformat()

        return adapted_knowledge

    async def record_learning_experience(
        self, agent: BiomimeticAgent, task: Dict[str, Any], result: Dict[str, Any]
    ):
        """Record a learning experience for future inheritance."""
        experience_id = f"exp_{agent.agent_id}_{int(datetime.now().timestamp())}"

        # Extract actions from task processing
        actions_taken = []
        if "processing_steps" in result:
            for step in result["processing_steps"]:
                actions_taken.append(
                    {
                        "action_type": step.get("type", "unknown"),
                        "parameters": step.get("parameters", {}),
                        "result": step.get("result", {}),
                        "success": step.get("success", False),
                        "effectiveness": step.get("effectiveness", 0.5),
                    }
                )
        else:
            # Create a single action from the overall result
            actions_taken.append(
                {
                    "action_type": "task_processing",
                    "parameters": task,
                    "result": result,
                    "success": result.get("success", False),
                    "effectiveness": 1.0 if result.get("success", False) else 0.0,
                }
            )

        # Extract lessons learned
        lessons_learned = []
        if result.get("success", False):
            lessons_learned.append(
                f"Successful {task.get('task_type', 'task')} processing"
            )
            if result.get("fallback_used", False):
                lessons_learned.append("Fallback strategy was effective")
        else:
            lessons_learned.append(f"Failed {task.get('task_type', 'task')} processing")
            if "error" in result:
                lessons_learned.append(f"Error encountered: {result['error']}")

        # Create learning experience
        experience = LearningExperience(
            experience_id=experience_id,
            task_type=task.get("task_type", "unknown"),
            context={
                "environmental_factors": agent.environmental_factors.copy(),
                "agent_mood": agent.current_mood.value,
                "task_complexity": task.get("complexity", 0.5),
            },
            actions_taken=actions_taken,
            outcome=result,
            lessons_learned=lessons_learned,
            effectiveness_metrics={
                "success": result.get("success", False),
                "processing_time": result.get("processing_time", 0.0),
                "energy_efficiency": 1.0 / max(0.1, result.get("energy_consumed", 0.1)),
                "pattern_recognition": agent.genome.get_effective_expression(
                    GeneticBase.MEMORY
                ),
            },
            agent_state={
                "agent_id": agent.agent_id,
                "archetype": agent.archetype.value,
                "generation": agent.genome.generation,
                "genetic_profile": {
                    base.name.lower(): agent.genome.get_effective_expression(base)
                    for base in GeneticBase
                },
            },
            timestamp=datetime.now(),
        )

        # Add to knowledge base
        self.knowledge_base.add_learning_experience(experience)

        logger.debug(
            f"Recorded learning experience {experience_id} for agent {agent.agent_id}"
        )

    def get_inheritance_statistics(self) -> Dict[str, Any]:
        """Get statistics about knowledge inheritance across generations."""
        total_fragments = len(self.knowledge_base.knowledge_fragments)
        total_experiences = len(self.knowledge_base.learning_experiences)

        # Calculate archetype distribution
        archetype_distribution = {}
        for archetype, fragment_ids in self.knowledge_base.archetype_knowledge.items():
            archetype_distribution[archetype.value] = len(fragment_ids)

        # Calculate knowledge type distribution
        type_distribution = defaultdict(int)
        for fragment in self.knowledge_base.knowledge_fragments.values():
            type_distribution[fragment.knowledge_type] += 1

        # Calculate effectiveness distribution
        effectiveness_scores = [
            f.effectiveness_score
            for f in self.knowledge_base.knowledge_fragments.values()
        ]

        avg_effectiveness = (
            sum(effectiveness_scores) / len(effectiveness_scores)
            if effectiveness_scores
            else 0.0
        )

        return {
            "total_knowledge_fragments": total_fragments,
            "total_learning_experiences": total_experiences,
            "archetype_distribution": archetype_distribution,
            "knowledge_type_distribution": dict(type_distribution),
            "average_effectiveness": avg_effectiveness,
            "inheritance_success_rates": self.knowledge_base.inheritance_success_rates.copy(),
        }

    def save_knowledge_base(self, filepath: str):
        """Save the knowledge base to file."""
        data = {
            "knowledge_fragments": {
                fid: {
                    "fragment_id": f.fragment_id,
                    "knowledge_type": f.knowledge_type,
                    "content": f.content,
                    "source_agent_id": f.source_agent_id,
                    "source_generation": f.source_generation,
                    "effectiveness_score": f.effectiveness_score,
                    "usage_count": f.usage_count,
                    "creation_time": f.creation_time.isoformat(),
                    "last_used": f.last_used.isoformat(),
                    "archetype_affinity": f.archetype_affinity,
                    "genetic_requirements": f.genetic_requirements,
                }
                for fid, f in self.knowledge_base.knowledge_fragments.items()
            },
            "archetype_knowledge": {
                archetype.value: fragment_ids
                for archetype, fragment_ids in self.knowledge_base.archetype_knowledge.items()
            },
            "inheritance_success_rates": self.knowledge_base.inheritance_success_rates,
            "system_parameters": {
                "inheritance_rate": self.inheritance_rate,
                "adaptation_rate": self.adaptation_rate,
                "forgetting_rate": self.forgetting_rate,
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved knowledge base to {filepath}")

    def load_knowledge_base(self, filepath: str):
        """Load knowledge base from file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        # Restore knowledge fragments
        self.knowledge_base.knowledge_fragments = {}
        for fid, fdata in data["knowledge_fragments"].items():
            fragment = KnowledgeFragment(
                fragment_id=fdata["fragment_id"],
                knowledge_type=fdata["knowledge_type"],
                content=fdata["content"],
                source_agent_id=fdata["source_agent_id"],
                source_generation=fdata["source_generation"],
                effectiveness_score=fdata["effectiveness_score"],
                usage_count=fdata["usage_count"],
                creation_time=datetime.fromisoformat(fdata["creation_time"]),
                last_used=datetime.fromisoformat(fdata["last_used"]),
                archetype_affinity=fdata["archetype_affinity"],
                genetic_requirements=fdata["genetic_requirements"],
            )
            self.knowledge_base.knowledge_fragments[fid] = fragment

        # Restore archetype knowledge
        self.knowledge_base.archetype_knowledge = {}
        for archetype_name, fragment_ids in data["archetype_knowledge"].items():
            archetype = Archetype(archetype_name)
            self.knowledge_base.archetype_knowledge[archetype] = fragment_ids

        # Restore other data
        self.knowledge_base.inheritance_success_rates = data[
            "inheritance_success_rates"
        ]

        if "system_parameters" in data:
            params = data["system_parameters"]
            self.inheritance_rate = params.get("inheritance_rate", 0.7)
            self.adaptation_rate = params.get("adaptation_rate", 0.3)
            self.forgetting_rate = params.get("forgetting_rate", 0.1)

        logger.info(
            f"Loaded knowledge base from {filepath}: "
            f"{len(self.knowledge_base.knowledge_fragments)} fragments"
        )
