#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neuromorphic Scheduler Module for Phoenix DemiGod

This module implements a task scheduler inspired by spiking neural networks,
enabling efficient resource allocation and task prioritization based on
temporal dynamics and system load.
"""

import heapq
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable, Any

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/neuromorphic_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NeuromorphicScheduler")

class Neuron:
    """
    Represents a spiking neuron with leaky integrate-and-fire dynamics.
    
    Attributes:
        threshold (float): Firing threshold
        rest_potential (float): Resting membrane potential
        membrane_potential (float): Current membrane potential
        refractory_period (float): Time after firing during which neuron cannot fire again
        refractory_until (float): Time until neuron can fire again
        leak_rate (float): Rate at which membrane potential decays towards rest
        last_spike (float): Time of last spike
        spike_count (int): Number of spikes produced
    """
    
    def __init__(
        self,
        threshold: float = 1.0,
        rest_potential: float = 0.0,
        refractory_period: float = 1.0,
        leak_rate: float = 0.1
    ):
        """
        Initialize a spiking neuron.
        
        Args:
            threshold: Firing threshold
            rest_potential: Resting membrane potential
            refractory_period: Time after firing during which neuron cannot fire again
            leak_rate: Rate at which membrane potential decays towards rest
        """
        self.threshold = threshold
        self.rest_potential = rest_potential
        self.membrane_potential = rest_potential
        self.refractory_period = refractory_period
        self.refractory_until = 0.0
        self.leak_rate = leak_rate
        self.last_spike = 0.0
        self.spike_count = 0
    
    def inject_current(self, current: float, time_now: float) -> bool:
        """
        Inject current into the neuron and check if it spikes.
        
        Args:
            current: Input current
            time_now: Current simulation time
            
        Returns:
            True if the neuron spikes, False otherwise
        """
        # Update membrane potential considering leak since last update
        time_since_last_spike = time_now - self.last_spike
        if time_since_last_spike > 0:
            # Apply leak
            self.membrane_potential = self.rest_potential + (self.membrane_potential - self.rest_potential) * \
                                      np.exp(-self.leak_rate * time_since_last_spike)
        
        # If in refractory period, current has no effect
        if time_now < self.refractory_until:
            return False
        
        # Add current to membrane potential
        self.membrane_potential += current
        
        # Check for spike
        if self.membrane_potential >= self.threshold:
            # Neuron spikes
            self.last_spike = time_now
            self.spike_count += 1
            self.refractory_until = time_now + self.refractory_period
            self.membrane_potential = self.rest_potential
            return True
        else:
            self.last_spike = time_now
            return False
    
    def reset(self) -> None:
        """Reset neuron to initial state."""
        self.membrane_potential = self.rest_potential
        self.refractory_until = 0.0
        self.last_spike = 0.0
        self.spike_count = 0


class TaskNeuronGroup:
    """
    Group of neurons representing a task or process to be scheduled.
    
    Attributes:
        name (str): Name of the task
        priority (float): Priority of the task
        neurons (List[Neuron]): Neurons in the group
        spike_history (List[Tuple[float, int]]): History of spikes
        creation_time (float): Time when the task was created
        activation_threshold (int): Number of neuron spikes needed to activate task
        activation_count (int): Number of activations so far
        task_function (Callable): Function to execute when task is activated
        refractory_period (float): Time after activation during which task cannot be activated again
        refractory_until (float): Time until task can be activated again
    """
    
    def __init__(
        self,
        name: str,
        priority: float,
        num_neurons: int = 5,
        activation_threshold: int = 3,
        task_function: Callable = None,
        refractory_period: float = 5.0,
        neuron_params: Dict = None
    ):
        """
        Initialize a group of neurons representing a task.
        
        Args:
            name: Name of the task
            priority: Priority of the task
            num_neurons: Number of neurons in the group
            activation_threshold: Number of neuron spikes needed to activate task
            task_function: Function to execute when task is activated
            refractory_period: Time after activation during which task cannot be activated again
            neuron_params: Parameters for neuron initialization
        """
        self.name = name
        self.priority = priority
        self.activation_threshold = activation_threshold
        self.task_function = task_function
        self.refractory_period = refractory_period
        self.refractory_until = 0.0
        self.creation_time = time.time()
        self.activation_count = 0
        
        # Configure neurons
        neuron_params = neuron_params or {}
        self.neurons = [Neuron(**neuron_params) for _ in range(num_neurons)]
        self.spike_history = []
    
    def stimulate(self, current_values: List[float], time_now: float) -> bool:
        """
        Stimulate neurons in the group and check if task should activate.
        
        Args:
            current_values: Input currents for each neuron
            time_now: Current simulation time
            
        Returns:
            True if the task should be activated, False otherwise
        """
        if time_now < self.refractory_until:
            return False
        
        # Ensure current_values matches number of neurons
        if len(current_values) != len(self.neurons):
            current_values = current_values[:len(self.neurons)] if len(current_values) > len(self.neurons) else \
                            current_values + [0.0] * (len(self.neurons) - len(current_values))
        
        # Inject current into each neuron
        spike_count = 0
        for i, (neuron, current) in enumerate(zip(self.neurons, current_values)):
            if neuron.inject_current(current, time_now):
                spike_count += 1
                self.spike_history.append((time_now, i))
        
        # Check if activation threshold is reached
        if spike_count >= self.activation_threshold:
            self.activation_count += 1
            self.refractory_until = time_now + self.refractory_period
            return True
        
        return False
    
    def execute_task(self, *args, **kwargs) -> Any:
        """
        Execute the task function.
        
        Args:
            *args: Arguments to pass to the task function
            **kwargs: Keyword arguments to pass to the task function
            
        Returns:
            Result of the task function
        """
        if self.task_function is None:
            logger.warning(f"No task function defined for task {self.name}")
            return None
        
        try:
            start_time = time.time()
            result = self.task_function(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"Task {self.name} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            logger.error(f"Error executing task {self.name}: {str(e)}")
            return None
    
    def get_recent_activity(self, window: float = 10.0, time_now: float = None) -> float:
        """
        Get the recent activity level of the neuron group.
        
        Args:
            window: Time window to consider (in seconds)
            time_now: Current time (if None, use current time)
            
        Returns:
            Activity level (spikes per second)
        """
        if time_now is None:
            time_now = time.time()
        
        # Count spikes in the window
        recent_spikes = [t for t, _ in self.spike_history if time_now - window <= t <= time_now]
        
        # Calculate spikes per second
        return len(recent_spikes) / window if window > 0 else 0


class NeuromorphicScheduler:
    """
    Neuromorphic task scheduler using spiking neural networks.
    
    Attributes:
        task_groups (Dict[str, TaskNeuronGroup]): Task groups to schedule
        network_time (float): Current network simulation time
        task_queue (List): Priority queue of pending tasks
        executed_tasks (List[str]): List of executed task names
        resource_monitor (Callable): Function to monitor system resources
        adaptation_rate (float): Rate at which neuron parameters adapt to system state
    """
    
    def __init__(
        self,
        resource_monitor: Callable = None,
        adaptation_rate: float = 0.1,
        time_scale: float = 1.0
    ):
        """
        Initialize the neuromorphic scheduler.
        
        Args:
            resource_monitor: Function to monitor system resources
            adaptation_rate: Rate at which neuron parameters adapt to system state
            time_scale: Time scaling factor for simulation
        """
        self.task_groups = {}
        self.network_time = 0.0
        self.task_queue = []  # Priority queue (heap)
        self.executed_tasks = []
        self.resource_monitor = resource_monitor
        self.adaptation_rate = adaptation_rate
        self.time_scale = time_scale
        self.last_update = time.time()
        
        logger.info("NeuromorphicScheduler initialized")
    
    def add_task(
        self,
        name: str,
        priority: float,
        task_function: Callable,
        num_neurons: int = 5,
        activation_threshold: int = 3,
        refractory_period: float = 5.0,
        neuron_params: Dict = None
    ) -> TaskNeuronGroup:
        """
        Add a task to the scheduler.
        
        Args:
            name: Name of the task
            priority: Priority of the task
            task_function: Function to execute when task is activated
            num_neurons: Number of neurons in the task group
            activation_threshold: Number of neuron spikes needed to activate task
            refractory_period: Time after activation during which task cannot be activated again
            neuron_params: Parameters for neuron initialization
            
        Returns:
            The created task group
        """
        task_group = TaskNeuronGroup(
            name=name,
            priority=priority,
            num_neurons=num_neurons,
            activation_threshold=activation_threshold,
            task_function=task_function,
            refractory_period=refractory_period,
            neuron_params=neuron_params
        )
        
        self.task_groups[name] = task_group
        logger.info(f"Added task '{name}' with priority {priority}")
        
        return task_group
    
    def remove_task(self, name: str) -> bool:
        """
        Remove a task from the scheduler.
        
        Args:
            name: Name of the task to remove
            
        Returns:
            True if the task was removed, False if it wasn't found
        """
        if name in self.task_groups:
            del self.task_groups[name]
            logger.info(f"Removed task '{name}'")
            return True
        else:
            logger.warning(f"Task '{name}' not found")
            return False
    
    def update(self, delta_time: float = None) -> None:
        """
        Update the neural network simulation.
        
        Args:
            delta_time: Time step for the update (if None, use real elapsed time)
        """
        current_time = time.time()
        
        if delta_time is None:
            delta_time = (current_time - self.last_update) * self.time_scale
        
        self.network_time += delta_time
        
        # Get system resources if monitor is available
        system_resources = None
        if self.resource_monitor is not None:
            try:
                system_resources = self.resource_monitor()
            except Exception as e:
                logger.error(f"Error monitoring system resources: {str(e)}")
        
        # Update all task groups
        for name, task_group in self.task_groups.items():
            # Generate input currents based on task priority, age, and system resources
            currents = self._generate_currents(task_group, system_resources)
            
            # Stimulate the task group
            if task_group.stimulate(currents, self.network_time):
                # Task is activated, add to queue
                task_priority = -task_group.priority  # Negate priority for min-heap
                heapq.heappush(self.task_queue, (task_priority, name, self.network_time))
                logger.debug(f"Task '{name}' activated and added to queue with priority {-task_priority}")
        
        self.last_update = current_time
    
    def _generate_currents(
        self,
        task_group: TaskNeuronGroup,
        system_resources: Dict = None
    ) -> List[float]:
        """
        Generate input currents for a task group based on various factors.
        
        Args:
            task_group: The task group to generate currents for
            system_resources: Current system resources
            
        Returns:
            List of current values for each neuron in the task group
        """
        num_neurons = len(task_group.neurons)
        base_currents = [0.0] * num_neurons
        
        # Factor 1: Base current from task priority
        priority_current = task_group.priority * 0.1
        
        # Factor 2: Time-dependent current (increases the longer a task waits)
        age = self.network_time - task_group.creation_time
        age_factor = np.tanh(age / 100.0)  # Saturating function
        age_current = age_factor * 0.05
        
        # Factor 3: Resource-dependent current
        resource_current = 0.0
        if system_resources is not None:
            # More resources = more current
            cpu_idle = system_resources.get('cpu_idle', 50) / 100.0
            memory_free = system_resources.get('memory_free', 50) / 100.0
            
            # If resources are scarce, high-priority tasks get more current
            resource_factor = (cpu_idle + memory_free) / 2.0
            resource_current = resource_factor * 0.1 * task_group.priority
        
        # Combine all factors
        for i in range(num_neurons):
            # Base current plus some noise for variety
            noise = np.random.normal(0, 0.01)
            base_currents[i] = priority_current + age_current + resource_current + noise
            
            # First neuron gets higher current to represent "readiness"
            if i == 0:
                base_currents[i] *= 1.2
        
        return base_currents
    
    def step(self) -> Optional[str]:
        """
        Execute the highest priority task in the queue.
        
        Returns:
            Name of the executed task, or None if no task was executed
        """
        if not self.task_queue:
            return None
        
        # Get the highest priority task
        _, task_name, activation_time = heapq.heappop(self.task_queue)
        task_group = self.task_groups.get(task_name)
        
        if task_group is None:
            logger.warning(f"Task '{task_name}' not found, may have been removed")
            return None
        
        # Execute the task
        logger.info(f"Executing task '{task_name}' (activated at {activation_time:.2f})")
        task_group.execute_task()
        
        # Record execution
        self.executed_tasks.append(task_name)
        
        return task_name
    
    def run_cycle(self, max_steps: int = 1, delta_time: float = 0.1) -> List[str]:
        """
        Run a complete update-step cycle.
        
        Args:
            max_steps: Maximum number of tasks to execute
            delta_time: Time step for the update
            
        Returns:
            List of executed task names
        """
        self.update(delta_time)
        
        executed = []
        for _ in range(max_steps):
            task_name = self.step()
            if task_name is None:
                break
            executed.append(task_name)
        
        return executed
    
    def get_statistics(self) -> Dict:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary of statistics
        """
        task_stats = {}
        for name, task_group in self.task_groups.items():
            task_stats[name] = {
                'priority': task_group.priority,
                'activations': task_group.activation_count,
                'recent_activity': task_group.get_recent_activity(window=30.0, time_now=self.network_time)
            }
        
        task_counts = {}
        for task_name in self.executed_tasks:
            task_counts[task_name] = task_counts.get(task_name, 0) + 1
        
        # Calculate fairness index (Jain's fairness index)
        if task_counts:
            values = list(task_counts.values())
            fairness = (sum(values) ** 2) / (len(values) * sum(x**2 for x in values))
        else:
            fairness = 1.0
        
        return {
            'time': self.network_time,
            'queue_length': len(self.task_queue),
            'executed_tasks': len(self.executed_tasks),
            'task_counts': task_counts,
            'fairness_index': fairness,
            'task_stats': task_stats
        }
    
    def adapt_parameters(self) -> None:
        """
        Adapt neuron parameters based on system performance and fairness.
        """
        stats = self.get_statistics()
        fairness = stats['fairness_index']
        
        # If fairness is low, adjust neuron parameters to favor under-executed tasks
        if fairness < 0.8:
            task_counts = stats['task_counts']
            total_executions = sum(task_counts.values()) if task_counts else 1
            
            for name, task_group in self.task_groups.items():
                execution_ratio = task_counts.get(name, 0) / total_executions
                
                # If task is under-executed relative to its priority, increase sensitivity
                expected_ratio = task_group.priority / sum(tg.priority for tg in self.task_groups.values())
                
                if execution_ratio < expected_ratio:
                    # Increase sensitivity by lowering threshold or increasing neuron excitability
                    for neuron in task_group.neurons:
                        neuron.threshold *= (1 - self.adaptation_rate)
                else:
                    # Decrease sensitivity
                    for neuron in task_group.neurons:
                        neuron.threshold *= (1 + self.adaptation_rate)
            
            logger.info(f"Adapted neuron parameters based on fairness index {fairness:.3f}")


class ResourceMonitor:
    """
    Monitor system resources for the neuromorphic scheduler.
    
    Attributes:
        cpu_history (List[float]): History of CPU usage
        memory_history (List[float]): History of memory usage
        history_length (int): Maximum length of history
    """
    
    def __init__(self, history_length: int = 10):
        """
        Initialize the resource monitor.
        
        Args:
            history_length: Maximum length of resource history
        """
        self.cpu_history = []
        self.memory_history = []
        self.history_length = history_length
    
    def get_resources(self) -> Dict[str, float]:
        """
        Get current system resources.
        
        Returns:
            Dictionary of resource usage
        """
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_history.append(cpu_percent)
            if len(self.cpu_history) > self.history_length:
                self.cpu_history.pop(0)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_history.append(memory_percent)
            if len(self.memory_history) > self.history_length:
                self.memory_history.pop(0)
            
            return {
                'cpu_used': cpu_percent,
                'cpu_idle': 100 - cpu_percent,
                'memory_used': memory_percent,
                'memory_free': 100 - memory_percent,
                'cpu_trend': self._calculate_trend(self.cpu_history),
                'memory_trend': self._calculate_trend(self.memory_history)
            }
        except ImportError:
            logger.warning("psutil not available, returning default resource values")
            return {
                'cpu_used': 50,
                'cpu_idle': 50,
                'memory_used': 50,
                'memory_free': 50,
                'cpu_trend': 0,
                'memory_trend': 0
            }
    
    def _calculate_trend(self, history: List[float]) -> float:
        """
        Calculate the trend of a resource metric.
        
        Args:
            history: History of resource values
            
        Returns:
            Trend value (-1 to 1, where positive means increasing)
        """
        if len(history) < 2:
            return 0
        
        # Simple linear regression slope
        x = list(range(len(history)))
        y = history
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_xx = sum(x_i ** 2 for x_i in x)
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
            # Normalize to [-1, 1]
            return max(min(slope * 10, 1), -1)  # Scale and clamp
        except ZeroDivisionError:
            return 0


def example_usage():
    """Example usage of the neuromorphic scheduler."""
    # Create a resource monitor
    resource_monitor = ResourceMonitor()
    
    # Create a scheduler
    scheduler = NeuromorphicScheduler(
        resource_monitor=resource_monitor.get_resources,
        adaptation_rate=0.05
    )
    
    # Define some task functions
    def high_priority_task():
        print("Executing high priority task")
        time.sleep(0.1)
    
    def medium_priority_task():
        print("Executing medium priority task")
        time.sleep(0.2)
    
    def low_priority_task():
        print("Executing low priority task")
        time.sleep(0.3)
    
    # Add tasks with different priorities
    scheduler.add_task(
        name="high_priority",
        priority=0.9,
        task_function=high_priority_task,
        num_neurons=5,
        activation_threshold=2
    )
    
    scheduler.add_task(
        name="medium_priority",
        priority=0.5,
        task_function=medium_priority_task,
        num_neurons=5,
        activation_threshold=3
    )
    
    scheduler.add_task(
        name="low_priority",
        priority=0.2,
        task_function=low_priority_task,
        num_neurons=5,
        activation_threshold=4
    )
    
    # Run the scheduler for 10 cycles
    print("Running scheduler for 10 cycles...")
    for i in range(10):
        executed = scheduler.run_cycle(max_steps=3, delta_time=0.5)
        print(f"Cycle {i+1}: Executed tasks: {executed}")
        
        # Adapt parameters every 3 cycles
        if (i + 1) % 3 == 0:
            scheduler.adapt_parameters()
    
    # Print statistics
    stats = scheduler.get_statistics()
    print("\nScheduler Statistics:")
    print(f"Total tasks executed: {stats['executed_tasks']}")
    print(f"Task execution counts: {stats['task_counts']}")
    print(f"Fairness index: {stats['fairness_index']:.3f}")


if __name__ == "__main__":
    example_usage()
