"""
Custom simulation module to avoid circular imports
"""

import numpy as np

class SimulationResults:
    """Mock simulation results"""
    def __init__(self):
        # Create mock data for model and market swaption implied values
        self.model_swaption_implied = {
            'key1': [0.1, 0.2, 0.3, 0.4],
            'key2': [0.15, 0.25, 0.35, 0.45],
            'key3': [0.12, 0.22, 0.32, 0.42],
            'key4': [0.11, 0.21, 0.31, 0.41]
        }
        self.market_swaption_implied = {
            'key1': [0.11, 0.21, 0.31, 0.41],
            'key2': [0.16, 0.26, 0.36, 0.46],
            'key3': [0.13, 0.23, 0.33, 0.43],
            'key4': [0.12, 0.22, 0.32, 0.42]
        }

class Simulation:
    """Mock Simulation class"""
    def __init__(self, market_data_obj, num_paths, frequency, expiries, cms_tenors, coterminal, maturity, simulation_dates):
        print(f"Initializing simulation with {num_paths} paths")
        self.market_data_obj = market_data_obj
        self.num_paths = num_paths
        self.frequency = frequency
        self.expiries = expiries
        self.cms_tenors = cms_tenors
        self.coterminal = coterminal
        self.maturity = maturity
        self.simulation_dates = simulation_dates
        self.results = SimulationResults()
    
    def run_simulation(self, diffusion_ids, market, simulation_dates):
        """Run the simulation"""
        print(f"Running simulation with {len(diffusion_ids)} diffusion IDs")
        # In a real implementation, this would run the actual simulation
        # For now, we just use the mock results
        pass
    
    def plot(self, simulation_dates):
        """Generate plots"""
        print("Generating plots (mock implementation)")
        pass

# Create a simulation module with the Simulation class
class SimulationModule:
    def __init__(self):
        self.Simulation = Simulation

# Create a singleton instance
simulation = SimulationModule()
