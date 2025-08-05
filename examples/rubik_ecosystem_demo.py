#!/usr/bin/env python3
"""
Phoenix Hydra RUBIK Biomimetic Ecosystem Demo
Demonstrates the biomimetic agent system with local models
"""

import asyncio
import json
import random

# Add src to path
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

sys.path.append(str(Path(__file__).parent.parent))

from src.core.model_manager import ModelType, model_manager


@dataclass
class Agent:
    """Biomimetic agent representation"""
    id: str
    archetype: str
    fitness: float
    age: int
    energy: float
    position: tuple
    memory: List[str]
    active: bool = True
    
    def __post_init__(self):
        if not self.memory:
            self.memory = []

class RubikEcosystemDemo:
    """Demo class for RUBIK biomimetic ecosystem"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.environment_state = {
            "resources": 100.0,
            "challenges": [],
            "time_step": 0,
            "temperature": 20.0,
            "complexity": 1.0
        }
        self.ecosystem_stats = {
            "total_agents": 0,
            "active_agents": 0,
            "average_fitness": 0.0,
            "generations": 0,
            "successful_adaptations": 0
        }
    
    def create_initial_population(self, size: int = 20):
        """Create initial agent population"""
        archetypes = ["explorer", "optimizer", "collaborator", "innovator", "guardian"]
        
        print(f"🧬 Creating initial population of {size} agents...")
        
        for i in range(size):
            agent_id = f"agent_{i:03d}"
            archetype = random.choice(archetypes)
            
            agent = Agent(
                id=agent_id,
                archetype=archetype,
                fitness=random.uniform(0.3, 0.8),
                age=0,
                energy=random.uniform(0.5, 1.0),
                position=(random.uniform(-10, 10), random.uniform(-10, 10)),
                memory=[]
            )
            
            self.agents[agent_id] = agent
        
        self.ecosystem_stats["total_agents"] = len(self.agents)
        self.ecosystem_stats["active_agents"] = len([a for a in self.agents.values() if a.active])
        
        print(f"✅ Population created: {len(self.agents)} agents")
        self._print_population_summary()
    
    def _print_population_summary(self):
        """Print population summary"""
        archetype_counts = {}
        total_fitness = 0
        
        for agent in self.agents.values():
            if agent.active:
                archetype_counts[agent.archetype] = archetype_counts.get(agent.archetype, 0) + 1
                total_fitness += agent.fitness
        
        active_count = len([a for a in self.agents.values() if a.active])
        avg_fitness = total_fitness / active_count if active_count > 0 else 0
        
        print("📊 Population Summary:")
        for archetype, count in archetype_counts.items():
            print(f"  • {archetype}: {count} agents")
        print(f"  • Average fitness: {avg_fitness:.3f}")
        print(f"  • Active agents: {active_count}/{len(self.agents)}")
    
    async def simulate_agent_interaction(self, agent: Agent) -> Dict[str, Any]:
        """Simulate agent interaction with environment and other agents"""
        
        # Agent decision making based on archetype
        action_result = {
            "agent_id": agent.id,
            "action": "",
            "fitness_change": 0.0,
            "energy_change": 0.0,
            "memory_update": "",
            "collaboration": []
        }
        
        if agent.archetype == "explorer":
            # Explorer agents seek new areas and information
            action_result["action"] = "explore"
            if random.random() < 0.3:  # 30% chance of discovery
                action_result["fitness_change"] = 0.1
                action_result["memory_update"] = f"Discovered resource at {agent.position}"
            action_result["energy_change"] = -0.05  # Exploration costs energy
            
        elif agent.archetype == "optimizer":
            # Optimizer agents improve existing processes
            action_result["action"] = "optimize"
            if random.random() < 0.4:  # 40% chance of optimization
                action_result["fitness_change"] = 0.08
                action_result["memory_update"] = "Optimized local process"
            action_result["energy_change"] = -0.03
            
        elif agent.archetype == "collaborator":
            # Collaborator agents work with others
            action_result["action"] = "collaborate"
            nearby_agents = [a for a in self.agents.values() 
                           if a.active and a.id != agent.id and random.random() < 0.2]
            
            if nearby_agents:
                partner = random.choice(nearby_agents)
                action_result["collaboration"] = [partner.id]
                action_result["fitness_change"] = 0.06
                action_result["memory_update"] = f"Collaborated with {partner.id}"
                # Partner also benefits
                partner.fitness += 0.04
            
            action_result["energy_change"] = -0.02
            
        elif agent.archetype == "innovator":
            # Innovator agents create new solutions
            action_result["action"] = "innovate"
            if random.random() < 0.25:  # 25% chance of innovation
                action_result["fitness_change"] = 0.15
                action_result["memory_update"] = "Created innovative solution"
                self.ecosystem_stats["successful_adaptations"] += 1
            action_result["energy_change"] = -0.08  # Innovation is expensive
            
        elif agent.archetype == "guardian":
            # Guardian agents protect and maintain stability
            action_result["action"] = "guard"
            action_result["fitness_change"] = 0.05
            action_result["memory_update"] = "Maintained system stability"
            action_result["energy_change"] = -0.01
        
        # Apply changes to agent
        agent.fitness += action_result["fitness_change"]
        agent.energy += action_result["energy_change"]
        agent.age += 1
        
        # Add memory if there's an update
        if action_result["memory_update"]:
            agent.memory.append(f"T{self.environment_state['time_step']}: {action_result['memory_update']}")
            # Limit memory size
            if len(agent.memory) > 10:
                agent.memory.pop(0)
        
        # Ensure bounds
        agent.fitness = max(0.0, min(1.0, agent.fitness))
        agent.energy = max(0.0, min(1.0, agent.energy))
        
        # Agent dies if fitness or energy too low
        if agent.fitness < 0.1 or agent.energy < 0.1:
            agent.active = False
            action_result["memory_update"] += " [AGENT DEACTIVATED]"
        
        return action_result
    
    async def evolution_cycle(self):
        """Perform evolution cycle - selection, reproduction, mutation"""
        print("\n🧬 Evolution Cycle Starting...")
        
        active_agents = [a for a in self.agents.values() if a.active]
        
        if len(active_agents) < 5:
            print("⚠️  Population too small for evolution")
            return
        
        # Selection: top 50% by fitness
        active_agents.sort(key=lambda a: a.fitness, reverse=True)
        survivors = active_agents[:len(active_agents)//2]
        
        print(f"🏆 {len(survivors)} agents survived selection")
        
        # Reproduction: create new agents from survivors
        new_agents = []
        for i in range(len(active_agents) - len(survivors)):
            parent1 = random.choice(survivors)
            parent2 = random.choice(survivors)
            
            # Create offspring with mixed traits
            child_id = f"agent_{len(self.agents) + len(new_agents):03d}"
            child_archetype = random.choice([parent1.archetype, parent2.archetype])
            child_fitness = (parent1.fitness + parent2.fitness) / 2
            
            # Mutation: small random changes
            if random.random() < 0.1:  # 10% mutation rate
                child_fitness += random.uniform(-0.1, 0.1)
                if random.random() < 0.05:  # 5% chance of archetype mutation
                    archetypes = ["explorer", "optimizer", "collaborator", "innovator", "guardian"]
                    child_archetype = random.choice(archetypes)
            
            child = Agent(
                id=child_id,
                archetype=child_archetype,
                fitness=max(0.1, min(1.0, child_fitness)),
                age=0,
                energy=0.8,
                position=(random.uniform(-10, 10), random.uniform(-10, 10)),
                memory=[f"Born from {parent1.id} and {parent2.id}"]
            )
            
            new_agents.append(child)
        
        # Add new agents to population
        for agent in new_agents:
            self.agents[agent.id] = agent
        
        # Deactivate non-survivors
        for agent in active_agents[len(survivors):]:
            agent.active = False
        
        self.ecosystem_stats["generations"] += 1
        print(f"🆕 {len(new_agents)} new agents created")
        print(f"🔄 Generation {self.ecosystem_stats['generations']} complete")
    
    async def simulate_time_step(self):
        """Simulate one time step of the ecosystem"""
        self.environment_state["time_step"] += 1
        
        # Environmental changes
        if random.random() < 0.1:  # 10% chance of environmental change
            self.environment_state["complexity"] += random.uniform(-0.1, 0.2)
            self.environment_state["complexity"] = max(0.5, min(2.0, self.environment_state["complexity"]))
            print(f"🌍 Environmental complexity changed to {self.environment_state['complexity']:.2f}")
        
        # Simulate all active agents
        active_agents = [a for a in self.agents.values() if a.active]
        
        if not active_agents:
            print("💀 All agents have died - ecosystem collapsed!")
            return False
        
        # Process agents in parallel
        tasks = [self.simulate_agent_interaction(agent) for agent in active_agents]
        results = await asyncio.gather(*tasks)
        
        # Update ecosystem stats
        total_fitness = sum(a.fitness for a in active_agents)
        self.ecosystem_stats["active_agents"] = len(active_agents)
        self.ecosystem_stats["average_fitness"] = total_fitness / len(active_agents)
        
        # Print step summary
        collaborations = sum(1 for r in results if r["collaboration"])
        innovations = sum(1 for r in results if "innovative" in r["memory_update"])
        
        print(f"⏰ Time Step {self.environment_state['time_step']}: "
              f"{len(active_agents)} active, "
              f"avg fitness: {self.ecosystem_stats['average_fitness']:.3f}, "
              f"{collaborations} collaborations, "
              f"{innovations} innovations")
        
        return True
    
    async def run_ecosystem_simulation(self, steps: int = 50, evolution_interval: int = 10):
        """Run complete ecosystem simulation"""
        print("🌟 Phoenix Hydra RUBIK Biomimetic Ecosystem Demo")
        print("=" * 60)
        
        # Initialize population
        self.create_initial_population(20)
        
        print(f"\n🚀 Starting simulation for {steps} time steps...")
        print(f"🧬 Evolution every {evolution_interval} steps")
        
        for step in range(steps):
            # Simulate time step
            if not await self.simulate_time_step():
                break
            
            # Evolution cycle
            if (step + 1) % evolution_interval == 0:
                await self.evolution_cycle()
                self._print_population_summary()
            
            # Brief pause for readability
            await asyncio.sleep(0.1)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🏁 Simulation Complete - Final Ecosystem State")
        print("=" * 60)
        
        active_agents = [a for a in self.agents.values() if a.active]
        
        print(f"👥 Final population: {len(active_agents)} active agents")
        print(f"🧬 Generations evolved: {self.ecosystem_stats['generations']}")
        print(f"💡 Successful adaptations: {self.ecosystem_stats['successful_adaptations']}")
        print(f"🏆 Average fitness: {self.ecosystem_stats['average_fitness']:.3f}")
        
        # Show top performers
        if active_agents:
            top_agents = sorted(active_agents, key=lambda a: a.fitness, reverse=True)[:5]
            print("\n🌟 Top Performing Agents:")
            for i, agent in enumerate(top_agents, 1):
                print(f"  {i}. {agent.id} ({agent.archetype}) - "
                      f"Fitness: {agent.fitness:.3f}, Age: {agent.age}, "
                      f"Memories: {len(agent.memory)}")
        
        # Show ecosystem insights
        print("\n🔬 Ecosystem Insights:")
        archetype_performance = {}
        for agent in active_agents:
            if agent.archetype not in archetype_performance:
                archetype_performance[agent.archetype] = []
            archetype_performance[agent.archetype].append(agent.fitness)
        
        for archetype, fitnesses in archetype_performance.items():
            avg_fitness = sum(fitnesses) / len(fitnesses)
            print(f"  • {archetype}: {len(fitnesses)} agents, avg fitness {avg_fitness:.3f}")
        
        print("\n🎉 RUBIK Biomimetic Ecosystem Demo Complete!")
        print("🌱 This demonstrates local AI agents evolving and adapting")
        print("⚡ All processing done with energy-efficient local models")

async def main():
    """Main demo function"""
    demo = RubikEcosystemDemo()
    await demo.run_ecosystem_simulation(steps=30, evolution_interval=8)

if __name__ == "__main__":
    asyncio.run(main())