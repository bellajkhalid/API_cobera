#!/usr/bin/env python
"""
Lognormal FX with MHJM Rates model implementation (MOCK VERSION)
This script provides a mock implementation for the Lognormal FX with MHJM Rates endpoint
"""

import json
import sys
import argparse
import numpy as np

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Lognormal FX with MHJM Rates model')
    parser.add_argument('--num-paths', type=int, default=524288,
                        help='Number of simulation paths')
    parser.add_argument('--volatility', type=float, default=0.15,
                        help='FX volatility')
    return parser.parse_args()

def generate_mock_data(num_paths, volatility):
    """
    Generate mock data for the Lognormal FX with MHJM Rates model
    
    Args:
        num_paths (int): Number of simulation paths
        volatility (float): FX volatility
        
    Returns:
        dict: Mock data for the model
    """
    # Generate mock strikes
    strikes = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    
    # Generate mock volatilities
    np.random.seed(42)  # For reproducibility
    model_volatility = [volatility * (1 + 0.1 * np.sin(i/2)) for i in range(len(strikes))]
    market_volatility = [volatility * (1 + 0.05 * np.cos(i/3)) for i in range(len(strikes))]
    
    # Generate mock money market and discount factor results
    results_money_market = [0.001 * i for i in range(len(strikes))]
    results_discount_factors = [0.99 - 0.01 * i for i in range(len(strikes))]
    
    # Create response data
    response = {
        "status": "success",
        "data": {
            "strikes": strikes,
            "model_volatility": model_volatility,
            "market_volatility": market_volatility,
            "results_money_market": results_money_market,
            "results_discount_factors": results_discount_factors,
            "parameters": {
                "num_paths": num_paths,
                "volatility": volatility
            }
        },
        "error": None
    }
    
    return response

def main():
    """Main entry point"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Generate mock data
        result = generate_mock_data(args.num_paths, args.volatility)
        
        # Print result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        # Return error response
        error_response = {
            "status": "error",
            "data": None,
            "error": str(e)
        }
        print(json.dumps(error_response))
        sys.exit(1)

if __name__ == "__main__":
    main()
