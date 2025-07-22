#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Topological Data Analysis Module for Phoenix DemiGod

This module implements tools for analyzing data using topological methods,
enabling the detection of complex patterns and structures in high-dimensional data.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple, Union, Callable
from sklearn.neighbors import NearestNeighbors
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/topological_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TopologicalAnalysis")

class PersistentHomology:
    """
    Implementation of persistent homology for topological data analysis.
    
    Attributes:
        max_dimension (int): Maximum homology dimension to compute
        metric (str): Distance metric to use
        verbose (bool): Whether to print verbose output
    """
    
    def __init__(
        self,
        max_dimension: int = 1,
        metric: str = 'euclidean',
        verbose: bool = False
    ):
        """
        Initialize the persistent homology analyzer.
        
        Args:
            max_dimension: Maximum homology dimension to compute
            metric: Distance metric to use
            verbose: Whether to print verbose output
        """
        self.max_dimension = max_dimension
        self.metric = metric
        self.verbose = verbose
        self.diagrams = None
        
        logger.info(f"Initialized PersistentHomology with max_dimension={max_dimension}, metric={metric}")
    
    def fit(self, X: np.ndarray) -> 'PersistentHomology':
        """
        Compute persistent homology for the given data.
        
        Args:
            X: Input data array (n_samples, n_features)
            
        Returns:
            Self
        """
        if self.verbose:
            logger.info(f"Computing persistent homology for {X.shape[0]} points in {X.shape[1]} dimensions")
        
        # Compute distance matrix
        dist_matrix = squareform(pdist(X, metric=self.metric))
        
        # Compute persistence diagrams for each dimension
        self.diagrams = {}
        
        for dim in range(self.max_dimension + 1):
            if self.verbose:
                logger.info(f"Computing {dim}-dimensional persistence")
            
            # Compute filtration
            filtration = self._compute_filtration(dist_matrix, dim)
            
            # Compute persistence diagram
            diagram = self._compute_persistence(filtration, dim)
            
            self.diagrams[dim] = diagram
            
            if self.verbose:
                logger.info(f"Found {len(diagram)} {dim}-dimensional features")
        
        return self
    
    def _compute_filtration(self, dist_matrix: np.ndarray, dimension: int) -> List[Tuple]:
        """
        Compute the filtration for the given dimension.
        
        Args:
            dist_matrix: Distance matrix
            dimension: Homology dimension
            
        Returns:
            List of simplices in the filtration
        """
        n_samples = dist_matrix.shape[0]
        
        # Start with 0-simplices (vertices)
        filtration = [(i,) for i in range(n_samples)]
        
        # For 0-dimensional homology, we only need vertices
        if dimension == 0:
            return filtration
        
        # Compute higher dimensional simplices
        # For 1-dimensional homology, we need edges (pairs of vertices)
        if dimension >= 1:
            # Build edges based on the distance matrix
            edges = []
            for i in range(n_samples):
                for j in range(i+1, n_samples):
                    edges.append(((i, j), dist_matrix[i, j]))
            
            # Sort edges by distance
            edges.sort(key=lambda x: x[1])
            
            # Add edges to filtration
            for (i, j), dist in edges:
                filtration.append((i, j))
        
        # For 2-dimensional homology, we need faces (triplets of vertices)
        if dimension >= 2:
            # Build faces based on edges
            faces = []
            
            # For each possible triplet (i,j,k), check if all edges exist
            edge_set = set(e for e, _ in edges)
            for i in range(n_samples):
                for j in range(i+1, n_samples):
                    for k in range(j+1, n_samples):
                        if (i, j) in edge_set and (j, k) in edge_set and (i, k) in edge_set:
                            # Compute the maximum distance among the three edges
                            max_dist = max(dist_matrix[i, j], dist_matrix[j, k], dist_matrix[i, k])
                            faces.append(((i, j, k), max_dist))
            
            # Sort faces by maximum distance
            faces.sort(key=lambda x: x[1])
            
            # Add faces to filtration
            for (i, j, k), _ in faces:
                filtration.append((i, j, k))
        
        # Higher dimensions would follow a similar pattern
        
        return filtration
    
    def _compute_persistence(self, filtration: List[Tuple], dimension: int) -> List[Tuple[float, float]]:
        """
        Compute the persistence diagram for the given filtration and dimension.
        
        Args:
            filtration: List of simplices in the filtration
            dimension: Homology dimension
            
        Returns:
            Persistence diagram (list of birth-death pairs)
        """
        # This is a simplified implementation of persistence computation
        # In a real implementation, we would use a dedicated package like Dionysus or GUDHI
        
        if dimension == 0:
            # For 0-dimensional homology, we can use a simple union-find data structure
            # to track connected components
            
            # Initialize each vertex as its own component
            n_vertices = len([s for s in filtration if len(s) == 1])
            parent = list(range(n_vertices))
            birth = [0.0] * n_vertices  # All vertices are born at time 0
            death = [float('inf')] * n_vertices  # Initially, all components persist forever
            
            def find(x):
                if parent[x] != x:
                    parent[x] = find(parent[x])
                return parent[x]
            
            def union(x, y, time):
                x_root = find(x)
                y_root = find(y)
                
                if x_root == y_root:
                    return
                
                # The younger component dies and merges into the older one
                if birth[x_root] > birth[y_root]:
                    x_root, y_root = y_root, x_root
                
                # Record death time of the younger component
                death[y_root] = time
                
                # Merge components
                parent[y_root] = x_root
            
            # Process edges to merge connected components
            time = 0.0
            for simplex in filtration:
                if len(simplex) == 2:  # Edge
                    i, j = simplex
                    time += 0.01  # Increment time for each edge
                    union(i, j, time)
            
            # Collect birth-death pairs
            diagram = []
            for i in range(n_vertices):
                if find(i) == i:  # Root of a component
                    diagram.append((birth[i], float('inf')))  # The oldest component persists forever
                else:
                    if death[i] < float('inf'):
                        diagram.append((birth[i], death[i]))
            
            return diagram
        
        else:
            # For higher dimensions, we would need a proper implementation of
            # persistent homology computation, which is beyond the scope of this example
            
            # Return a placeholder
            return []
    
    def plot_diagram(self, dimension: int = 0, ax=None, max_death: float = None) -> None:
        """
        Plot the persistence diagram for the given dimension.
        
        Args:
            dimension: Homology dimension
            ax: Matplotlib axis (if None, a new one is created)
            max_death: Maximum death time to plot (if None, automatically determined)
        """
        if self.diagrams is None or dimension not in self.diagrams:
            raise ValueError("Persistence diagram not computed or dimension not available")
        
        diagram = self.diagrams[dimension]
        
        if not diagram:
            logger.warning(f"No {dimension}-dimensional features found")
            return
        
        if ax is None:
            _, ax = plt.subplots(figsize=(6, 6))
        
        # Extract birth and death times
        births = [b for b, d in diagram]
        deaths = [d if d < float('inf') else max_death for b, d in diagram]
        
        if max_death is None:
            max_death = max(deaths) * 1.1
        
        # Plot points
        ax.scatter(births, deaths, s=50, alpha=0.7)
        
        # Plot diagonal
        diag_min = min(births) if births else 0
        diag_max = max_death
        ax.plot([diag_min, diag_max], [diag_min, diag_max], 'k--', alpha=0.5)
        
        # Labels
        ax.set_xlabel('Birth')
        ax.set_ylabel('Death')
        ax.set_title(f'{dimension}-dimensional Persistence Diagram')
        
        # Set equal aspect ratio
        ax.set_aspect('equal', 'box')
        
        # Set limits
        ax.set_xlim(diag_min, diag_max)
        ax.set_ylim(diag_min, diag_max)
        
        return ax
    
    def plot_barcode(self, dimension: int = 0, ax=None, max_death: float = None) -> None:
        """
        Plot the persistence barcode for the given dimension.
        
        Args:
            dimension: Homology dimension
            ax: Matplotlib axis (if None, a new one is created)
            max_death: Maximum death time to plot (if None, automatically determined)
        """
        if self.diagrams is None or dimension not in self.diagrams:
            raise ValueError("Persistence diagram not computed or dimension not available")
        
        diagram = self.diagrams[dimension]
        
        if not diagram:
            logger.warning(f"No {dimension}-dimensional features found")
            return
        
        if ax is None:
            _, ax = plt.subplots(figsize=(8, 6))
        
        # Sort features by persistence (death - birth)
        sorted_features = sorted(
            diagram,
            key=lambda x: x[1] - x[0] if x[1] < float('inf') else float('inf'),
            reverse=True
        )
        
        # Set maximum death time for visualization
        if max_death is None:
            finite_deaths = [d for _, d in diagram if d < float('inf')]
            max_death = max(finite_deaths) * 1.1 if finite_deaths else 1.0
        
        # Plot bars
        for i, (birth, death) in enumerate(sorted_features):
            if death == float('inf'):
                ax.plot([birth, max_death], [i, i], 'k-', linewidth=2)
            else:
                ax.plot([birth, death], [i, i], 'k-', linewidth=2)
        
        # Labels
        ax.set_xlabel('Filtration Value')
        ax.set_ylabel('Features (sorted by persistence)')
        ax.set_title(f'{dimension}-dimensional Persistence Barcode')
        
        return ax
    
    def get_persistent_features(
        self,
        dimension: int = 0,
        persistence_threshold: float = 0.1
    ) -> List[Tuple[float, float]]:
        """
        Get the persistent features for the given dimension.
        
        Args:
            dimension: Homology dimension
            persistence_threshold: Minimum persistence value to consider a feature
            
        Returns:
            List of persistent features (birth, death)
        """
        if self.diagrams is None or dimension not in self.diagrams:
            raise ValueError("Persistence diagram not computed or dimension not available")
        
        diagram = self.diagrams[dimension]
        
        # Filter features by persistence (death - birth)
        persistent_features = []
        for birth, death in diagram:
            if death == float('inf') or death - birth >= persistence_threshold:
                persistent_features.append((birth, death))
        
        return persistent_features
    
    def get_persistence_landscape(
        self,
        dimension: int = 0,
        num_landscapes: int = 1,
        resolution: int = 100,
        max_value: float = None
    ) -> np.ndarray:
        """
        Compute the persistence landscape for the given dimension.
        
        Args:
            dimension: Homology dimension
            num_landscapes: Number of landscape layers to compute
            resolution: Resolution of the landscape
            max_value: Maximum filtration value (if None, automatically determined)
            
        Returns:
            Landscape array of shape (num_landscapes, resolution)
        """
        if self.diagrams is None or dimension not in self.diagrams:
            raise ValueError("Persistence diagram not computed or dimension not available")
        
        diagram = self.diagrams[dimension]
        
        if not diagram:
            return np.zeros((num_landscapes, resolution))
        
        # Determine the range of filtration values
        births = [b for b, _ in diagram]
        finite_deaths = [d for _, d in diagram if d < float('inf')]
        
        if not finite_deaths:
            max_death = max(births) * 2.0
        else:
            max_death = max(finite_deaths)
        
        if max_value is None:
            max_value = max_death * 1.1
        
        # Create a grid of x values
        grid = np.linspace(0, max_value, resolution)
        
        # Initialize the landscape
        landscape = np.zeros((num_landscapes, resolution))
        
        # For each point in the persistence diagram, add a tent function to the landscape
        for birth, death in diagram:
            if death == float('inf'):
                death = max_value
            
            # Compute tent function
            peak = (birth + death) / 2
            
            for i in range(resolution):
                x = grid[i]
                if birth <= x <= peak:
                    value = x - birth
                elif peak <= x <= death:
                    value = death - x
                else:
                    value = 0
                
                # Add to the landscape
                for j in range(num_landscapes):
                    if value > landscape[j, i]:
                        # Shift down existing values
                        if j + 1 < num_landscapes:
                            landscape[j+1:, i] = np.roll(landscape[j:-1, i], 1)
                        
                        landscape[j, i] = value
                        break
        
        return landscape


class Mapper:
    """
    Implementation of the Mapper algorithm for topological data analysis.
    
    Attributes:
        filter_function (Callable): Function to map data points to filter values
        num_intervals (int): Number of intervals for the filter function
        overlap_fraction (float): Fraction of overlap between intervals
        clusterer (object): Clustering algorithm to use for each fiber
        cover (List): Cover of the filter range
    """
    
    def __init__(
        self,
        filter_function: Callable = None,
        num_intervals: int = 10,
        overlap_fraction: float = 0.5,
        clusterer=None
    ):
        """
        Initialize the Mapper algorithm.
        
        Args:
            filter_function: Function to map data points to filter values
            num_intervals: Number of intervals for the filter function
            overlap_fraction: Fraction of overlap between intervals
            clusterer: Clustering algorithm to use for each fiber
        """
        self.filter_function = filter_function
        self.num_intervals = num_intervals
        self.overlap_fraction = overlap_fraction
        
        # Default to hierarchical clustering if not provided
        if clusterer is None:
            from sklearn.cluster import AgglomerativeClustering
            self.clusterer = AgglomerativeClustering(n_clusters=None, distance_threshold=0.5)
        else:
            self.clusterer = clusterer
        
        self.cover = None
        self.graph = None
        
        logger.info(f"Initialized Mapper with {num_intervals} intervals and {overlap_fraction} overlap")
    
    def fit_transform(self, X: np.ndarray) -> Dict:
        """
        Apply the Mapper algorithm to the data.
        
        Args:
            X: Input data array (n_samples, n_features)
            
        Returns:
            Graph representation of the data
        """
        # Apply filter function to get filter values
        if self.filter_function is None:
            # Default to the first principal component
            from sklearn.decomposition import PCA
            pca = PCA(n_components=1)
            filter_values = pca.fit_transform(X).flatten()
            logger.info("Using PCA as default filter function")
        else:
            filter_values = self.filter_function(X)
        
        # Create cover of the filter range
        filter_min = filter_values.min()
        filter_max = filter_values.max()
        
        interval_length = (filter_max - filter_min) / self.num_intervals
        overlap = interval_length * self.overlap_fraction
        
        self.cover = []
        for i in range(self.num_intervals):
            interval_min = filter_min + i * interval_length - overlap / 2
            interval_max = filter_min + (i + 1) * interval_length + overlap / 2
            
            # Ensure the intervals don't exceed the filter range
            interval_min = max(interval_min, filter_min)
            interval_max = min(interval_max, filter_max)
            
            self.cover.append((interval_min, interval_max))
        
        # Process each interval
        logger.info("Processing intervals...")
        nodes = {}
        edges = []
        
        for i, (interval_min, interval_max) in enumerate(self.cover):
            # Get points in this interval
            mask = (filter_values >= interval_min) & (filter_values <= interval_max)
            if not np.any(mask):
                continue
            
            points_indices = np.where(mask)[0]
            points = X[points_indices]
            
            # Cluster points in this interval
            if len(points) <= 1:
                # Only one point, no need to cluster
                clusters = [0]
            else:
                try:
                    # Try to use the provided clusterer
                    clusters = self.clusterer.fit_predict(points)
                except Exception as e:
                    # If the clusterer doesn't support precomputed distance matrix
                    logger.warning(f"Clustering failed: {e}. Using single cluster.")
                    clusters = np.zeros(len(points), dtype=int)
            
            # Create nodes for each cluster
            for cluster_id in np.unique(clusters):
                node_id = f"{i}_{cluster_id}"
                cluster_indices = points_indices[clusters == cluster_id]
                
                nodes[node_id] = {
                    "interval": i,
                    "cluster": cluster_id,
                    "points": cluster_indices.tolist(),
                    "size": len(cluster_indices)
                }
        
        # Create edges between nodes with common points
        for node1_id, node1 in nodes.items():
            for node2_id, node2 in nodes.items():
                if node1_id >= node2_id:  # Avoid duplicate edges
                    continue
                
                # Check if the nodes share any points
                common_points = set(node1["points"]) & set(node2["points"])
                if common_points:
                    edges.append({
                        "source": node1_id,
                        "target": node2_id,
                        "weight": len(common_points)
                    })
        
        self.graph = {
            "nodes": nodes,
            "edges": edges
        }
        
        logger.info(f"Mapper graph created with {len(nodes)} nodes and {len(edges)} edges")
        
        return self.graph
    
    def plot_graph(self, ax=None, node_color_map: Dict = None, layout: str = 'spring') -> None:
        """
        Plot the Mapper graph.
        
        Args:
            ax: Matplotlib axis (if None, a new one is created)
            node_color_map: Dictionary mapping node IDs to colors
            layout: Graph layout algorithm ('spring', 'spectral', 'circular')
        """
        if self.graph is None:
            raise ValueError("Mapper graph not computed")
        
        try:
            import networkx as nx
        except ImportError:
            logger.error("Networkx is required for plotting Mapper graphs")
            raise
        
        # Create networkx graph
        G = nx.Graph()
        
        # Add nodes
        for node_id, node_data in self.graph["nodes"].items():
            G.add_node(node_id, **node_data)
        
        # Add edges
        for edge in self.graph["edges"]:
            G.add_edge(edge["source"], edge["target"], weight=edge["weight"])
        
        # Create layout
        if layout == 'spring':
            pos = nx.spring_layout(G)
        elif layout == 'spectral':
            pos = nx.spectral_layout(G)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        else:
            raise ValueError(f"Unknown layout: {layout}")
        
        # Create plot
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 8))
        
        # Node sizes based on number of points
        node_sizes = [node_data["size"] * 10 for node_data in self.graph["nodes"].values()]
        
        # Node colors
        if node_color_map is None:
            # Color nodes by interval
            node_colors = [node_data["interval"] for node_data in self.graph["nodes"].values()]
        else:
            node_colors = [node_color_map[node_id] for node_id in self.graph["nodes"].keys()]
        
        # Edge weights
        edge_weights = [edge["weight"] for edge in self.graph["edges"]]
        
        # Draw the graph
        nx.draw_networkx(
            G,
            pos=pos,
            with_labels=False,
            node_size=node_sizes,
            node_color=node_colors,
            cmap=plt.cm.viridis,
            width=edge_weights,
            alpha=0.8,
            ax=ax
        )
        
        ax.set_title('Mapper Graph')
        ax.axis('off')
        
        return ax


if __name__ == "__main__":
    # Example usage
    from sklearn.datasets import make_circles
    
    # Generate example data
    X, y = make_circles(n_samples=100, noise=0.05, factor=0.3, random_state=42)
    
    # Persistent Homology example
    ph = PersistentHomology(max_dimension=1, verbose=True)
    ph.fit(X)
    
    # Plot persistence diagram
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    ph.plot_diagram(dimension=0)
    
    plt.subplot(1, 2, 2)
    ph.plot_barcode(dimension=0)
    
    plt.tight_layout()
    plt.savefig("persistence_analysis.png")
    
    # Mapper example
    mapper = Mapper(num_intervals=5, overlap_fraction=0.3)
    graph = mapper.fit_transform(X)
    
    # Plot mapper graph
    plt.figure(figsize=(8, 8))
    node_color_map = {node_id: y[node_data["points"][0]] for node_id, node_data in graph["nodes"].items()}
    mapper.plot_graph(node_color_map=node_color_map)
    
    plt.savefig("mapper_graph.png")
