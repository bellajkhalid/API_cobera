import sys
import json
import numpy as np
from xsigmamodules.Math import (
    hartmanWatsonDistribution,
    gaussianQuadrature,
    hartman_watson_distribution_type,
)
from xsigmamodules.Vectorization import vector, matrix, tensor
from xsigma.util.numpy_support import xsigmaToNumpy, numpyToXsigma
from dataclasses import dataclass
from typing import Dict, List, Union

@dataclass
class CalculationParams:
    n: int
    t: float
    size_roots: int
    x_0: float
    x_n: float

    @classmethod
    def from_argv(cls, argv: List[str]) -> 'CalculationParams':
        if len(argv) < 6:
            raise ValueError("Required arguments: n t size_roots x_0 x_n")
        
        try:
            return cls(
                n=int(argv[1]),
                t=float(argv[2]),
                size_roots=int(argv[3]),
                x_0=float(argv[4]),
                x_n=float(argv[5])
            )
        except ValueError as e:
            raise ValueError(f"Error parsing arguments: {e}")

def calculate_hartman_watson_data(params: CalculationParams) -> Dict[str, Union[List[float], None]]:
    try:
        # Initialize vectors for calculation
        roots = vector["double"](params.size_roots)
        w1 = vector["double"](params.size_roots)
        w2 = vector["double"](params.size_roots)

        # Calculate Gaussian-Kronrod quadrature
        gaussianQuadrature.gauss_kronrod(params.size_roots, roots, w1, w2)
        
        # Create input points array
        a = np.linspace(params.x_0, params.x_n, params.n)
        r = numpyToXsigma(a)
        
        # Initialize result array
        b = np.zeros(params.n)
        result = numpyToXsigma(b)

        # Calculate distribution
        hartmanWatsonDistribution.distribution(
            result,
            params.t,
            r,
            roots,
            w1,
            hartman_watson_distribution_type.MIXTURE
        )

        # Convert result back to numpy array
        final_result = xsigmaToNumpy(result)

        return {
            "x_values": a.tolist(),
            "distribution": final_result.tolist()
        }
    except Exception as e:
        return {
            "x_values": None,
            "distribution": None,
            "error": str(e)
        }

def main() -> None:
    try:
        params = CalculationParams.from_argv(sys.argv)
        data = calculate_hartman_watson_data(params)
        
        response = {
            "status": "success",
            "data": data,
            "error": None
        }

    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "error": str(e)
        }

    print(json.dumps(response))

if __name__ == "__main__":
    main()