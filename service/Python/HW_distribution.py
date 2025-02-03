#!/usr/bin/env python3

import sys
import json
import numpy as np
from xsigmamodules.Math import (
    hartmanWatsonDistribution,
    gaussianQuadrature,
    hartman_watson_distribution_type,
)
from xsigmamodules.Vectorization import vector, matrix, tensor
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma

def calculate_hw_distribution(n, t, size_roots, x_0, x_n):
    try:
        # Create vectors for Gaussian quadrature
        roots = vector["double"](size_roots)
        w1 = vector["double"](size_roots)
        w2 = vector["double"](size_roots)

        # Calculate Gaussian quadrature weights and roots
        gaussianQuadrature.gauss_kronrod(size_roots, roots, w1, w2)

        # Create x values array
        x_values = np.linspace(x_0, x_n, n)
        r = numpyToXsigma(x_values)

        # Initialize result array
        distribution = np.zeros(n)
        result = numpyToXsigma(distribution)

        # Calculate Hartman-Watson distribution
        hartmanWatsonDistribution.distribution(
            result,
            t,
            r,
            roots,
            w1,
            hartman_watson_distribution_type.MIXTURE
        )

        # Convert back to numpy array for output
        distribution = xsigmaToNumpy(result)

        # Return results in the expected format
        output = {
            "status": "success",
            "data": {
                "x_values": x_values.tolist(),
                "distribution": distribution.tolist()
            },
            "error": None
        }

        return output

    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "error": str(e)
        }

def main():
    try:
        # Get command line arguments
        if len(sys.argv) != 6:
            raise ValueError("Expected 5 arguments: n, t, size_roots, x_0, x_n")

        n = int(sys.argv[1])
        t = float(sys.argv[2])
        size_roots = int(sys.argv[3])
        x_0 = float(sys.argv[4])
        x_n = float(sys.argv[5])

        # Validate inputs
        if n <= 0:
            raise ValueError("n must be positive")
        if t <= 0:
            raise ValueError("t must be positive")
        if size_roots <= 0:
            raise ValueError("size_roots must be positive")
        if x_0 >= x_n:
            raise ValueError("x_0 must be less than x_n")

        # Calculate distribution
        result = calculate_hw_distribution(n, t, size_roots, x_0, x_n)
        
        # Print result as JSON
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "data": None,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()