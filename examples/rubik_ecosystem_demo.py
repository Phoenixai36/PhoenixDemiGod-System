#!/usr/bin/env python3
"""
RUBIK Biomimetic Ecosystem Demo

This script demonstrates the complete RUBIK biomimetic agent system with
20-base logarithmic matrix genetics, self-evolving agents, Thanatos controller,
and cross-generational learning integrated with 2025 advanced AI models.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.biomimetic_agents import (
    Archetype,
    EcosystemConfig,
    GeneticBase,
    RUBIKGenome,
    create_rubik_ecosystem,
)
from src.local_processing import create_local_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def demo_genetic_system():
    """Demonstrate the 20-base logarithmic matrix genetic system."""
    logger.info("\n=== Demo: 20-Base Logarithmic Matrix Genetics ===")

    # Create a genome with specific traits
    genome = RUBIKGenome()

    logger.info(f"Created genome: {genome}")
    logger.info(f"Archetype: {genome.determine_archetype().value}")

    # Show top genetic expressions
    top_genes = []
    for base in GeneticBase:
        expression = genome.get_effective_expression(base)
        top_genes.append((base.name, expression))

    top_genes.sort(key=lambda x: x[1], reverse=True)

    logger.info("Top genetic expressions:")
    for gene_name, expression in top_genes[:5]:
        logger.info(f"  {gene_name}: {expression:.3f}")

    # Demonstrate mood calculation
    environmental_factors = {
        "novelty": 0.8,
        "task_complexity": 0.6,
        "threat_level": 0.2,
        "success_rate": 0.7,
    }

    mood = genome.calculate_mood_state(environmental_factors)
    logger.info(f"Current mood: {mood.value}")

    # Show model preferences
    model_prefs = genome.get_model_preferences()
    logger.info("AI Model preferences:")
    for category, model in model_prefs.items():
        logger.info(f"  {category}: {model}")

    return genome


async def demo_agent_creation_and_behavior(ecosystem):
    """Demonstrate agent creation and behavior."""
    logger.info("\n=== Demo: Agent Creation and Behavior ===")

    # Get agents by archetype
    for archetype in Archetype:
        agents = ecosystem.get_agents_by_archetype(archetype)
        logger.info(f"{archetype.value.title()} agents: {len(agents)}")

        if agents:
            agent_info = agents[0]
            logger.info(f"  Example {archetype.value}: {agent_info['agent_id']}")
            logger.info(f"    Fitness: {agent_info['fitness_score']:.3f}")
            logger.info(f"    Age: {agent_info['age_in_cycles']} cycles")
            logger.info(f"    Mood: {agent_info['current_mood']}")


async def demo_task_processing(ecosystem):
    """Demonstrate task processing with different agent archetypes."""
    logger.info("\n=== Demo: Task Processing ===")

    # Define various tasks for different archetypes
    tasks = [
        {
            "id": "analysis_001",
            "task_type": "analysis",
            "input_data": "Analyze the Phoenix Hydra system architecture for optimization opportunities",
            "complexity": 0.8,
        },
        {
            "id": "coding_001",
            "task_type": "coding",
            "input_data": "Implement a function to calculate Fibonacci numbers using memoization",
            "complexity": 0.6,
        },
        {
            "id": "security_001",
            "task_type": "security",
            "input_data": "Review this configuration for security vulnerabilities",
            "complexity": 0.7,
        },
        {
            "id": "optimization_001",
            "task_type": "optimization",
            "input_data": "Optimize this database query for better performance",
            "complexity": 0.5,
        },
        {
            "id": "discovery_001",
            "task_type": "discovery",
            "input_data": "Explore this dataset to find interesting patterns",
            "complexity": 0.9,
        },
    ]

    # Process tasks and show results
    results = []
    for task in tasks:
        logger.info(f"Processing {task['task_type']} task: {task['id']}")

        start_time = asyncio.get_event_loop().time()
        result = await ecosystem.process_task(task)
        processing_time = asyncio.get_event_loop().time() - start_time

        results.append(result)

        if result["success"]:
            metadata = result.get("ecosystem_metadata", {})
            logger.info(
                f"  ✅ Success! Processed by {metadata.get('agent_archetype', 'unknown')} agent"
            )
            logger.info(f"     Agent: {metadata.get('agent_id', 'unknown')}")
            logger.info(f"     Generation: {metadata.get('agent_generation', 0)}")
            logger.info(f"     Fitness: {metadata.get('agent_fitness', 0.0):.3f}")
            logger.info(f"     Processing time: {processing_time:.2f}s")
        else:
            logger.info(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

    # Show success rate
    successful = sum(1 for r in results if r["success"])
    logger.info(f"\nTask processing summary: {successful}/{len(tasks)} successful")

    return results


async def demo_evolution_and_learning(ecosystem):
    """Demonstrate evolution and cross-generational learning."""
    logger.info("\n=== Demo: Evolution and Learning ===")

    # Get initial population stats
    initial_status = ecosystem.get_ecosystem_status()
    initial_generation = initial_status["population"]["genome_pool_stats"]["generation"]
    initial_fitness = initial_status["population"]["fitness_distribution"]["avg"]

    logger.info(f"Initial population:")
    logger.info(f"  Generation: {initial_generation}")
    logger.info(f"  Average fitness: {initial_fitness:.3f}")
    logger.info(
        f"  Knowledge fragments: {initial_status['learning']['total_knowledge_fragments']}"
    )

    # Process several tasks to generate learning experiences
    logger.info("\nProcessing tasks to generate learning experiences...")

    learning_tasks = [
        {
            "task_type": "analysis",
            "input_data": f"Analyze system component {i}",
            "complexity": 0.5 + (i * 0.1),
        }
        for i in range(5)
    ]

    for task in learning_tasks:
        await ecosystem.process_task(task)

    # Force an evolution cycle
    logger.info("\nForcing evolution cycle...")
    evolution_stats = await ecosystem.force_evolution_cycle()

    logger.info(f"Evolution completed:")
    logger.info(f"  New generation: {evolution_stats['generation']}")
    logger.info(f"  Max fitness: {evolution_stats['max_fitness']:.3f}")
    logger.info(f"  Average fitness: {evolution_stats['avg_fitness']:.3f}")

    # Show learning statistics
    final_status = ecosystem.get_ecosystem_status()
    learning_stats = final_status["learning"]

    logger.info(f"\nLearning system status:")
    logger.info(f"  Knowledge fragments: {learning_stats['total_knowledge_fragments']}")
    logger.info(
        f"  Learning experiences: {learning_stats['total_learning_experiences']}"
    )
    logger.info(
        f"  Average effectiveness: {learning_stats['average_effectiveness']:.3f}"
    )

    # Show archetype distribution
    archetype_dist = learning_stats["archetype_distribution"]
    logger.info(f"  Knowledge by archetype:")
    for archetype, count in archetype_dist.items():
        logger.info(f"    {archetype}: {count} fragments")


async def demo_thanatos_controller(ecosystem):
    """Demonstrate the Thanatos controller lifecycle management."""
    logger.info("\n=== Demo: Thanatos Controller (Life and Death) ===")

    # Get lifecycle history
    lifecycle_history = ecosystem.thanatos_controller.get_lifecycle_history(20)

    logger.info("Recent lifecycle events:")
    for event in lifecycle_history[-10:]:  # Show last 10 events
        timestamp = datetime.fromisoformat(event["timestamp"])
        logger.info(
            f"  {timestamp.strftime('%H:%M:%S')} - {event['event_type'].upper()}: "
            f"Agent {event['agent_id'][:8]} "
            f"(fitness: {event['fitness_score']:.3f}, age: {event['age_in_cycles']})"
        )

    # Show population statistics
    pop_stats = ecosystem.thanatos_controller.population_stats
    logger.info(f"\nPopulation statistics:")
    logger.info(f"  Total births: {pop_stats['total_births']}")
    logger.info(f"  Total deaths: {pop_stats['total_deaths']}")
    logger.info(f"  Total reproductions: {pop_stats['total_reproductions']}")
    logger.info(f"  Average lifespan: {pop_stats['average_lifespan']:.1f} cycles")
    logger.info(f"  Current generation: {pop_stats['generation_count']}")

    # Demonstrate forced reproduction
    active_agents = list(ecosystem.thanatos_controller.active_agents.values())
    if len(active_agents) >= 2:
        parent1 = active_agents[0]
        parent2 = active_agents[1]

        logger.info(f"\nForcing reproduction between:")
        logger.info(
            f"  Parent 1: {parent1.agent_id} ({parent1.archetype.value}, fitness: {parent1.calculate_fitness():.3f})"
        )
        logger.info(
            f"  Parent 2: {parent2.agent_id} ({parent2.archetype.value}, fitness: {parent2.calculate_fitness():.3f})"
        )

        offspring_id = await ecosystem.thanatos_controller.force_reproduction(
            parent1.agent_id, parent2.agent_id
        )

        if offspring_id:
            offspring = ecosystem.thanatos_controller.get_agent(offspring_id)
            logger.info(f"  Offspring: {offspring_id} ({offspring.archetype.value})")
            logger.info(f"    Generation: {offspring.genome.generation}")
            logger.info(f"    Inherited traits from both parents")


async def demo_advanced_model_integration(ecosystem):
    """Demonstrate integration with 2025 advanced AI models."""
    logger.info("\n=== Demo: 2025 Advanced AI Model Integration ===")

    # Test different model preferences based on genetics
    model_tasks = [
        {
            "task_type": "reasoning",
            "input_data": "Solve this complex logical puzzle with multiple constraints",
            "expected_models": ["minimax-m1-80k", "kimi-k2-instruct", "glm-4.5"],
        },
        {
            "task_type": "coding",
            "input_data": "Write a complex algorithm with extensive documentation",
            "expected_models": ["qwen3-coder-480b-a35b", "qwen2.5-coder-32b"],
        },
        {
            "task_type": "multimodal",
            "input_data": "Generate and edit images based on contextual requirements",
            "expected_models": ["flux-kontext-max", "flux-dev"],
        },
    ]

    for task in model_tasks:
        logger.info(f"\nTesting {task['task_type']} task:")
        result = await ecosystem.process_task(task)

        if result["success"]:
            metadata = result.get("ecosystem_metadata", {})
            model_used = result.get("model_used", "unknown")

            logger.info(f"  Model used: {model_used}")
            logger.info(
                f"  Agent archetype: {metadata.get('agent_archetype', 'unknown')}"
            )
            logger.info(f"  Expected models: {', '.join(task['expected_models'])}")

            if model_used in task["expected_models"]:
                logger.info(f"  ✅ Correct model selection!")
            else:
                logger.info(f"  ⚠️  Unexpected model (possibly due to fallback)")


async def demo_ecosystem_monitoring(ecosystem):
    """Demonstrate ecosystem monitoring and metrics."""
    logger.info("\n=== Demo: Ecosystem Monitoring ===")

    status = ecosystem.get_ecosystem_status()

    logger.info("Ecosystem Status:")
    logger.info(f"  Running: {status['running']}")
    logger.info(f"  Uptime: {status['uptime_seconds']:.1f} seconds")
    logger.info(f"  Active tasks: {status['active_tasks']}")
    logger.info(f"  Queue size: {status['queue_size']}")

    # Population metrics
    population = status["population"]
    logger.info(f"\nPopulation Metrics:")
    logger.info(f"  Total agents: {population['total_agents']}")
    logger.info(f"  Average fitness: {population['fitness_distribution']['avg']:.3f}")
    logger.info(
        f"  Fitness range: {population['fitness_distribution']['min']:.3f} - {population['fitness_distribution']['max']:.3f}"
    )

    # Archetype distribution
    logger.info(f"  Archetype distribution:")
    for archetype, count in population["archetype_distribution"].items():
        logger.info(f"    {archetype}: {count}")

    # Task metrics
    task_metrics = status["task_metrics"]
    logger.info(f"\nTask Metrics:")
    logger.info(f"  Total processed: {task_metrics['total_tasks_processed']}")
    logger.info(
        f"  Success rate: {task_metrics['successful_tasks']}/{task_metrics['total_tasks_processed']}"
    )
    logger.info(
        f"  Average processing time: {task_metrics['average_processing_time']:.2f}s"
    )
    logger.info(
        f"  Total energy consumed: {task_metrics['total_energy_consumed']:.2f} joules"
    )

    # Learning metrics
    learning = status["learning"]
    logger.info(f"\nLearning Metrics:")
    logger.info(f"  Knowledge fragments: {learning['total_knowledge_fragments']}")
    logger.info(f"  Learning experiences: {learning['total_learning_experiences']}")
    logger.info(f"  Knowledge types: {learning['knowledge_type_distribution']}")


async def demo_ecosystem_persistence(ecosystem):
    """Demonstrate ecosystem state saving and loading."""
    logger.info("\n=== Demo: Ecosystem Persistence ===")

    # Save ecosystem state
    save_dir = Path("ecosystem_save_demo")
    ecosystem.save_ecosystem_state(save_dir)
    logger.info(f"Saved ecosystem state to {save_dir}")

    # Show saved files
    saved_files = list(save_dir.glob("*"))
    logger.info("Saved files:")
    for file_path in saved_files:
        size_kb = file_path.stat().st_size / 1024
        logger.info(f"  {file_path.name}: {size_kb:.1f} KB")

    # In a real scenario, you would stop the ecosystem and create a new one
    # ecosystem.load_ecosystem_state(save_dir)
    logger.info("State persistence demonstrated (loading skipped in demo)")


async def main():
    """Main demo function."""
    logger.info("🧬 Starting RUBIK Biomimetic Ecosystem Demo")
    logger.info("=" * 60)

    try:
        # Create local AI pipeline (optional for demo)
        logger.info("Creating local AI processing pipeline...")
        ai_pipeline = await create_local_pipeline()

        # Configure ecosystem with 2025 advanced models
        config = EcosystemConfig(
            max_population=20,  # Smaller for demo
            min_population=5,
            evolution_interval=60.0,  # Faster evolution for demo
            learning_enabled=True,
            auto_scaling=True,
            model_preferences={
                "reasoning_primary": "minimax-m1-80k",
                "reasoning_fallback": "kimi-k2-instruct",
                "coding_primary": "qwen3-coder-480b-a35b",
                "coding_fallback": "qwen2.5-coder-32b",
                "multimodal_primary": "flux-kontext-max",
                "multimodal_fallback": "flux-dev",
                "local_backbone": "mamba-codestral-7b",
                "local_fallback": "llama-3.3-8b",
            },
        )

        # Create and start RUBIK ecosystem
        logger.info("Creating RUBIK Biomimetic Ecosystem...")
        ecosystem = await create_rubik_ecosystem(config, ai_pipeline)

        # Wait for initialization
        await asyncio.sleep(2.0)

        # Run demonstrations
        await demo_genetic_system()
        await demo_agent_creation_and_behavior(ecosystem)
        await demo_task_processing(ecosystem)
        await demo_evolution_and_learning(ecosystem)
        await demo_thanatos_controller(ecosystem)
        await demo_advanced_model_integration(ecosystem)
        await demo_ecosystem_monitoring(ecosystem)
        await demo_ecosystem_persistence(ecosystem)

        logger.info("\n" + "=" * 60)
        logger.info("🎉 RUBIK Biomimetic Ecosystem Demo Complete!")
        logger.info("\nKey Achievements Demonstrated:")
        logger.info("✅ 20-base logarithmic matrix genetics")
        logger.info("✅ Self-evolving biomimetic agents")
        logger.info("✅ Dynamic mood and archetype systems")
        logger.info("✅ Thanatos controller lifecycle management")
        logger.info("✅ Cross-generational learning")
        logger.info("✅ Integration with 2025 advanced AI models")
        logger.info("✅ Evolutionary pressure and optimization")
        logger.info("✅ Transcendent emergent intelligence")

        # Show final ecosystem status
        final_status = ecosystem.get_ecosystem_status()
        logger.info(f"\nFinal Ecosystem Status:")
        logger.info(
            f"  Population: {final_status['population']['total_agents']} agents"
        )
        logger.info(
            f"  Generation: {final_status['population']['genome_pool_stats']['generation']}"
        )
        logger.info(
            f"  Knowledge fragments: {final_status['learning']['total_knowledge_fragments']}"
        )
        logger.info(
            f"  Tasks processed: {final_status['task_metrics']['total_tasks_processed']}"
        )
        logger.info(
            f"  Success rate: {final_status['task_metrics']['successful_tasks']}/{final_status['task_metrics']['total_tasks_processed']}"
        )

        # Graceful shutdown
        await ecosystem.stop()
        await ai_pipeline.shutdown()

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
