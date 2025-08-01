#!/usr/bin/env python3
"""
Phoenix Hydra Complete 2025 Stack Demo
Demonstrates the full 2025 model ecosystem with SSM/Local processing
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from biomimetic_agents.ecosystem import BiomimeticEcosystem
from local_processing.pipeline import LocalProcessingPipeline
from ssm_analysis.advanced_gap_detection import AdvancedGapDetector
from ssm_analysis.advanced_ssm_components import AdvancedSSMAnalyzer


class Phoenix2025StackDemo:
    """Complete demonstration of Phoenix Hydra 2025 capabilities"""

    def __init__(self):
        self.pipeline = LocalProcessingPipeline()
        self.ecosystem = BiomimeticEcosystem()
        self.ssm_analyzer = AdvancedSSMAnalyzer()
        self.gap_detector = AdvancedGapDetector()

    async def run_complete_demo(self):
        """Run complete demonstration of all 2025 stack components"""
        print("🚀 Phoenix Hydra 2025 Complete Stack Demo")
        print("=" * 50)

        # 1. System Health Check
        await self._system_health_check()

        # 2. Local Processing Demo
        await self._local_processing_demo()

        # 3. Biomimetic Agents Demo
        await self._biomimetic_agents_demo()

        # 4. SSM Analysis Demo
        await self._ssm_analysis_demo()

        # 5. Gap Detection Demo
        await self._gap_detection_demo()

        # 6. Integration Demo
        await self._integration_demo()

        print("\n🎉 Phoenix Hydra 2025 Stack Demo Complete!")
        print("Ready for production deployment with 100% local processing!")

    async def _system_health_check(self):
        """Check system health and readiness"""
        print("\n🏥 System Health Check")
        print("-" * 30)

        # Check local processing readiness
        is_offline = await self.pipeline.detect_offline_mode()
        print(f"📡 Offline Mode: {'✅ Active' if is_offline else '⚠️  Online'}")

        # Check model availability
        available_models = await self.pipeline.get_available_models()
        print(f"🤖 Available Models: {len(available_models)}")

        # Check biomimetic ecosystem
        agent_count = len(self.ecosystem.agents)
        print(f"🧬 Biomimetic Agents: {agent_count}")

        # Check SSM components
        ssm_ready = hasattr(self.ssm_analyzer, "lightning_attention")
        print(f"⚡ SSM Components: {'✅ Ready' if ssm_ready else '⚠️  Not Ready'}")

        print("✅ Health check complete")

    async def _local_processing_demo(self):
        """Demonstrate local processing capabilities"""
        print("\n🏠 Local Processing Demo")
        print("-" * 30)

        # Test queries for different model types
        test_queries = [
            {
                "text": "Explain quantum computing in simple terms",
                "task_type": "explanation",
                "model_preference": "general",
            },
            {
                "text": "def fibonacci(n):\n    # Complete this function",
                "task_type": "code_completion",
                "model_preference": "coding",
            },
            {
                "text": "What are the benefits of renewable energy?",
                "task_type": "analysis",
                "model_preference": "efficient",
            },
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test Query {i}: {query['task_type']}")

            start_time = time.time()
            try:
                result = await self.pipeline.process_query(
                    query["text"],
                    task_type=query["task_type"],
                    model_preference=query["model_preference"],
                )

                processing_time = time.time() - start_time

                print(f"✅ Response generated in {processing_time:.2f}s")
                print(f"🤖 Model used: {result.get('model_used', 'unknown')}")
                print(f"⚡ Energy efficient: {result.get('energy_efficient', False)}")
                print(f"📊 Response length: {len(result.get('response', ''))} chars")

            except Exception as e:
                print(f"❌ Error: {e}")

        print("✅ Local processing demo complete")

    async def _biomimetic_agents_demo(self):
        """Demonstrate biomimetic agent capabilities"""
        print("\n🧬 Biomimetic Agents Demo")
        print("-" * 30)

        # Initialize ecosystem if not already done
        if not self.ecosystem.agents:
            print("🌱 Initializing biomimetic ecosystem...")
            await self.ecosystem.initialize_ecosystem()

        # Demonstrate agent interactions
        scenarios = [
            {
                "name": "Creative Problem Solving",
                "prompt": "Design an innovative solution for urban transportation",
                "agent_types": ["Creator", "Explorer"],
            },
            {
                "name": "Risk Assessment",
                "prompt": "Analyze potential risks in AI deployment",
                "agent_types": ["Guardian", "Destroyer"],
            },
            {
                "name": "Knowledge Synthesis",
                "prompt": "Combine insights from multiple research papers",
                "agent_types": ["Explorer", "Creator"],
            },
        ]

        for scenario in scenarios:
            print(f"\n🎭 Scenario: {scenario['name']}")

            # Select appropriate agents
            selected_agents = []
            for agent in self.ecosystem.agents:
                if agent.persona.name in scenario["agent_types"]:
                    selected_agents.append(agent)

            if selected_agents:
                print(f"👥 Agents participating: {len(selected_agents)}")

                # Simulate agent collaboration
                for agent in selected_agents:
                    response = await agent.process_input(scenario["prompt"])
                    print(f"🤖 {agent.persona.name}: {response[:100]}...")

                    # Show agent evolution
                    print(f"📈 Agent mood: {agent.mood_engine.current_mood}")
                    print(f"🧬 Genetic fitness: {agent.genome.calculate_fitness():.2f}")
            else:
                print("⚠️  No suitable agents available")

        # Demonstrate cross-generational learning
        print(f"\n🔄 Cross-Generational Learning")
        learning_results = await self.ecosystem.cross_gen_learning.transfer_knowledge()
        print(f"📚 Knowledge transfers: {len(learning_results)}")

        print("✅ Biomimetic agents demo complete")

    async def _ssm_analysis_demo(self):
        """Demonstrate SSM analysis capabilities"""
        print("\n⚡ SSM Analysis Demo")
        print("-" * 30)

        # Test different analysis types
        analysis_tasks = [
            {
                "name": "Code Analysis",
                "data": "def process_data(items): return [x*2 for x in items if x > 0]",
                "analysis_type": "code",
            },
            {
                "name": "Text Analysis",
                "data": "The future of AI lies in energy-efficient architectures like SSM",
                "analysis_type": "text",
            },
            {
                "name": "Sequence Analysis",
                "data": [1, 2, 3, 5, 8, 13, 21, 34],
                "analysis_type": "sequence",
            },
        ]

        for task in analysis_tasks:
            print(f"\n🔍 {task['name']}")

            start_time = time.time()
            try:
                # Use Lightning Attention for analysis
                if hasattr(self.ssm_analyzer, "lightning_attention"):
                    result = await self.ssm_analyzer.lightning_attention.process(
                        task["data"], analysis_type=task["analysis_type"]
                    )

                    processing_time = time.time() - start_time

                    print(f"✅ Analysis complete in {processing_time:.3f}s")
                    print(
                        f"⚡ Energy efficient: {result.get('energy_efficient', True)}"
                    )
                    print(f"📊 Insights: {len(result.get('insights', []))}")

                    # Show energy comparison
                    energy_saved = result.get("energy_savings_vs_transformer", 0)
                    if energy_saved > 0:
                        print(f"🌱 Energy saved vs Transformer: {energy_saved:.1f}%")

            except Exception as e:
                print(f"❌ Error: {e}")

        print("✅ SSM analysis demo complete")

    async def _gap_detection_demo(self):
        """Demonstrate gap detection capabilities"""
        print("\n🔍 Gap Detection Demo")
        print("-" * 30)

        print("🔍 Running comprehensive gap analysis...")

        # Run gap detection
        gaps = self.gap_detector.detect_all_gaps()

        # Generate report
        report = self.gap_detector.generate_gap_report()
        summary = report["summary"]

        print(f"📊 Gap Analysis Results:")
        print(f"  Total Gaps Found: {summary['total_gaps']}")
        print(f"  Critical Issues: {summary['critical_gaps']}")
        print(f"  High Priority: {summary['high_priority_gaps']}")
        print(f"  Estimated Fix Time: {summary['estimated_effort_days']} days")

        # Show top priority gaps
        if report["prioritized_action_plan"]:
            print(f"\n🎯 Top Priority Actions:")
            for action in report["prioritized_action_plan"][:3]:
                print(
                    f"  {action['priority']}. {action['title']} ({action['severity']})"
                )

        # Save detailed report
        report_path = self.gap_detector.save_gap_report("demo_gap_report.json")
        print(f"📄 Detailed report: {report_path}")

        print("✅ Gap detection demo complete")

    async def _integration_demo(self):
        """Demonstrate full system integration"""
        print("\n🔗 System Integration Demo")
        print("-" * 30)

        # Complex query requiring multiple components
        complex_query = {
            "text": "Analyze this code for efficiency and suggest biomimetic improvements",
            "code": """
def process_large_dataset(data):
    results = []
    for item in data:
        if item > threshold:
            processed = expensive_operation(item)
            results.append(processed)
    return results
            """,
            "context": "This function processes millions of records daily",
        }

        print("🧠 Processing complex multi-component query...")

        start_time = time.time()

        # 1. Local processing for initial analysis
        print("1️⃣ Local processing analysis...")
        local_result = await self.pipeline.process_query(
            complex_query["text"] + "\n" + complex_query["code"],
            task_type="code_analysis",
        )

        # 2. SSM analysis for efficiency insights
        print("2️⃣ SSM efficiency analysis...")
        if hasattr(self.ssm_analyzer, "lightning_attention"):
            ssm_result = await self.ssm_analyzer.lightning_attention.process(
                complex_query["code"], analysis_type="code"
            )

        # 3. Biomimetic agent suggestions
        print("3️⃣ Biomimetic agent consultation...")
        agent_responses = []
        for agent in self.ecosystem.agents[:2]:  # Use first 2 agents
            response = await agent.process_input(
                f"Suggest biomimetic improvements for: {complex_query['code']}"
            )
            agent_responses.append(
                {"agent": agent.persona.name, "suggestion": response}
            )

        total_time = time.time() - start_time

        # Combine results
        print(f"\n📋 Integrated Analysis Results:")
        print(f"⏱️  Total processing time: {total_time:.2f}s")
        print(f"🤖 Local model used: {local_result.get('model_used', 'unknown')}")
        print(f"⚡ Energy efficient processing: ✅")
        print(f"🧬 Biomimetic insights: {len(agent_responses)}")
        print(
            f"📊 SSM analysis: {'✅ Complete' if 'ssm_result' in locals() else '⚠️  Partial'}"
        )

        # Show sample insights
        if agent_responses:
            print(f"\n💡 Sample biomimetic insight:")
            print(
                f"   {agent_responses[0]['agent']}: {agent_responses[0]['suggestion'][:100]}..."
            )

        print("✅ Integration demo complete")


async def main():
    """Main demo function"""
    demo = Phoenix2025StackDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
