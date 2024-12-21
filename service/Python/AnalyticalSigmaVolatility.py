import sys
import json
import numpy as np
from typing import Dict, List, Union, Tuple, Callable
from dataclasses import dataclass
from xsigmamodules.Util import analyticalSigmaVolatility, blackScholes
from xsigmamodules.Vectorization import vector
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma

@dataclass
class VolatilityParams:
    n: int
    fwd: float
    time: float
    ctrl_p: float
    ctrl_c: float
    atm: float
    skew: float
    smile: float
    put: float
    call: float
    test: int

    @classmethod
    def from_argv(cls, argv: List[str]) -> 'VolatilityParams':
        required_args = 11
        if len(argv) < required_args + 1:  # +1 for script name
            raise ValueError(
                "Required arguments: n fwd time ctrl_p ctrl_c atm skew smile put call test"
            )
        
        param_names = ['n', 'fwd', 'time', 'ctrl_p', 'ctrl_c', 'atm', 
                      'skew', 'smile', 'put', 'call', 'test']
        param_types = [int, float, float, float, float, float, 
                      float, float, float, float, int]
        
        try:
            params = {}
            for i, (name, type_) in enumerate(zip(param_names, param_types)):
                params[name] = type_(argv[i + 1])
            return cls(**params)
        except ValueError as e:
            raise ValueError(f"Error parsing argument {param_names[i]}: {e}")

class VolatilitySurfaceCalculator:
    def __init__(self, params: VolatilityParams):
        self.params = params
        
    def create_analytical_sigma_vol(self, ctrl_c: float = None) -> analyticalSigmaVolatility:
        """Create analyticalSigmaVolatility object with given parameters."""
        ctrl_c = ctrl_c if ctrl_c is not None else self.params.ctrl_c
        return analyticalSigmaVolatility(
            self.params.time, self.params.fwd, self.params.fwd,
            self.params.ctrl_p, ctrl_c, self.params.atm, self.params.skew,
            self.params.smile, self.params.put, self.params.call
        )

    def calculate_test1_volatility(self) -> Dict[str, List[float]]:
        """Calculate initial volatility surface."""
        strikes = np.linspace(0.25 * self.params.fwd, 2.0 * self.params.fwd, self.params.n)
        vols0 = np.full(self.params.n, self.params.atm)
        vols_origin = np.zeros(self.params.n)
        
        obj = self.create_analytical_sigma_vol()
        for vols in [vols0, vols_origin]:
            obj.asv(numpyToXsigma(vols), numpyToXsigma(strikes), True)

        return {
            "strikes": strikes.tolist(),
            "Tab_1": vols0.tolist(),
            "Tab_2": vols_origin.tolist()
        }

    def calculate_test2_volatility(self) -> Dict[str, List[float]]:
        """Calculate comparison of volatility surfaces."""
        strikes = np.linspace(0.3, 2.0, self.params.n)
        vols_minus = np.zeros(self.params.n)
        vols_plus = np.zeros(self.params.n)

        # Calculate surfaces with different control parameters
        self.create_analytical_sigma_vol().asv(
            numpyToXsigma(vols_plus), numpyToXsigma(strikes)
        )
        self.create_analytical_sigma_vol(ctrl_c=4.0).asv(
            numpyToXsigma(vols_minus), numpyToXsigma(strikes)
        )

        return {
            "strikes": strikes.tolist(),
            "Tab_1": vols_minus.tolist(),
            "Tab_2": vols_plus.tolist()
        }

    def calculate_sensitivities(self, strikes: np.ndarray) -> Tuple[np.ndarray, ...]:
        """Calculate volatility sensitivities."""
        sensitivityArrays = [np.zeros(self.params.n) for _ in range(11)]
        vols, *sensitivities = sensitivityArrays
        
        self.create_analytical_sigma_vol().asv_with_sensitivities(
            numpyToXsigma(strikes),
            *map(numpyToXsigma, sensitivityArrays)
        )
        
        return vols, *sensitivities

    def calculate_density_and_probability(self, 
                                       strikes: np.ndarray, 
                                       vols: np.ndarray,
                                       strike_sensitivity: np.ndarray,
                                       strike2_sensitivity: np.ndarray = None
                                       ) -> Tuple[List[float], List[float]]:
        """Calculate density and probability values."""
        density = []
        probability = []
        
        for i, strike in enumerate(strikes):
            if strike2_sensitivity is not None:
                density_value = blackScholes.density(
                    self.params.fwd, strike, self.params.time,
                    vols[i], strike_sensitivity[i], strike2_sensitivity[i]
                )
                density.append(density_value)
                
            proba_value = blackScholes.probability(
                self.params.fwd, strike, self.params.time,
                vols[i], strike_sensitivity[i]
            )
            probability.append(proba_value)
            
        return density, probability

    def calculate_bumped_values(self, strikes: np.ndarray) -> Tuple[List[float], List[float]]:
        """Calculate bumped density and probability values."""
        bump = 1e-6
        density_bump = []
        probability_bump = []

        for strike in strikes:
            strikes_tmp = np.array([strike - bump, strike, strike + bump])
            vols_tmp = np.zeros(3)
            
            self.create_analytical_sigma_vol().asv(
                numpyToXsigma(vols_tmp), numpyToXsigma(strikes_tmp)
            )

            prices = [
                blackScholes.price(self.params.fwd, k, self.params.time, v, 1.0, 1.0)
                for k, v in zip([strike - bump, strike, strike + bump], vols_tmp)
            ]
            
            density_bump.append((prices[2] + prices[0] - 2 * prices[1]) / (bump * bump))
            probability_bump.append(1 + (prices[2] - prices[0]) / (2.0 * bump))

        return density_bump, probability_bump

    def calculate_test3_density(self) -> Dict[str, List[float]]:
        """Calculate density surface."""
        strikes = np.linspace(0.3, 2.0, self.params.n)
        vols, *sensitivities = self.calculate_sensitivities(strikes)
        strike_sensitivity, *_, strike2_sensitivity = sensitivities[5:]
        
        density, _ = self.calculate_density_and_probability(
            strikes, vols, strike_sensitivity, strike2_sensitivity
        )
        density_bump, _ = self.calculate_bumped_values(strikes)

        return {
            "strikes": strikes.tolist(),
            "Tab_1": density,
            "Tab_2": density_bump
        }

    def calculate_test4_probability(self) -> Dict[str, List[float]]:
        """Calculate probability surface."""
        strikes = np.linspace(0.3, 2.0, self.params.n)
        vols, *sensitivities = self.calculate_sensitivities(strikes)
        strike_sensitivity = sensitivities[5]
        
        _, probability = self.calculate_density_and_probability(
            strikes, vols, strike_sensitivity
        )
        _, probability_bump = self.calculate_bumped_values(strikes)

        return {
            "strikes": strikes.tolist(),
            "Tab_1": probability,
            "Tab_2": probability_bump
        }

def main() -> None:
    try:
        params = VolatilityParams.from_argv(sys.argv)
        calculator = VolatilitySurfaceCalculator(params)
        
        test_functions = {
            1: calculator.calculate_test1_volatility,
            2: calculator.calculate_test2_volatility,
            3: calculator.calculate_test3_density,
            4: calculator.calculate_test4_probability
        }
        
        if params.test not in test_functions:
            raise ValueError(f"Invalid test case: {params.test}. Must be between 1 and 4.")
            
        data = test_functions[params.test]()
        response = {"status": "success", "data": data, "error": None}

    except Exception as e:
        response = {"status": "error", "data": None, "error": str(e)}

    print(json.dumps(response))

if __name__ == "__main__":
    main()