import sys
import json
import numpy as np
from typing import Dict, List, Union, Tuple
from dataclasses import dataclass
from xsigmamodules.Market import volatilityModelExtendedSvi
from xsigmamodules.Util import blackScholes, volatility_type
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
        if len(argv) < required_args + 1:
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

    def create_svi_model(self, ctrl_c: float = None) -> volatilityModelExtendedSvi:
        ctrl_c = ctrl_c if ctrl_c is not None else self.params.ctrl_c
        return volatilityModelExtendedSvi(
            self.params.fwd, self.params.ctrl_p, ctrl_c,
            self.params.atm, self.params.skew, self.params.smile,
            self.params.put, self.params.call
        )

    def calculate_test1_volatility(self) -> Dict[str, List[float]]:
        strikes = np.linspace(0.25 * self.params.fwd, 2.0 * self.params.fwd, self.params.n)
        vols = np.zeros(self.params.n)
        vols0 = np.full(self.params.n, self.params.atm)
        
        obj = self.create_svi_model()
        obj.implied_volatility(numpyToXsigma(vols), numpyToXsigma(strikes), 1.0, 
                             self.params.time, volatility_type.LOG_NORMAL)
        
        return {
            "strikes": strikes.tolist(),
            "Tab_1": vols.tolist(),
            "Tab_2": vols0.tolist()
        }

    def calculate_test2_volatility(self) -> Dict[str, List[float]]:
        strikes = np.linspace(0.3, 2.0, self.params.n)
        vols_minus = np.zeros(self.params.n)
        vols_plus = np.zeros(self.params.n)

        # Standard model
        self.create_svi_model().implied_volatility(
            numpyToXsigma(vols_plus), numpyToXsigma(strikes), 1.0,
            self.params.time, volatility_type.LOG_NORMAL
        )

        # Model with increased ctrl_c
        self.create_svi_model(ctrl_c=4.0).implied_volatility(
            numpyToXsigma(vols_minus), numpyToXsigma(strikes), 1.0,
            self.params.time, volatility_type.LOG_NORMAL
        )

        return {
            "strikes": strikes.tolist(),
            "Tab_1": vols_minus.tolist(),
            "Tab_2": vols_plus.tolist()
        }

    def calculate_sensitivities(self, strikes: np.ndarray) -> Tuple[np.ndarray, ...]:
        vols = np.zeros(self.params.n)
        sensitivities = [np.zeros(self.params.n) for _ in range(10)]
        
        self.create_svi_model().sensitivities(
            self.params.time,
            numpyToXsigma(strikes),
            numpyToXsigma(vols),
            *[numpyToXsigma(s) for s in sensitivities]
        )
        
        return (vols, *sensitivities)

    def calculate_density_and_probability(self, strikes: np.ndarray) -> Dict[str, List[float]]:
        bump = 1e-6
        density = []
        density_bump = []
        probability = []
        probability_bump = []
        
        vols, *sensitivities = self.calculate_sensitivities(strikes)
        strike_sensitivity = sensitivities[5]
        strike2_sensitivity = sensitivities[9]

        # Calculate analytical values
        for i, strike in enumerate(strikes):
            density.append(blackScholes.density(
                self.params.fwd, strike, self.params.time,
                vols[i], strike_sensitivity[i], strike2_sensitivity[i]
            ))
            probability.append(blackScholes.probability(
                self.params.fwd, strike, self.params.time,
                vols[i], strike_sensitivity[i]
            ))

        # Calculate bumped values
        for strike in strikes:
            strikes_tmp = np.array([strike - bump, strike, strike + bump])
            vols_tmp = np.zeros(3)
            
            self.create_svi_model().implied_volatility(
                numpyToXsigma(vols_tmp), numpyToXsigma(strikes_tmp), 1.0,
                self.params.time, volatility_type.LOG_NORMAL
            )

            prices = [
                blackScholes.price(self.params.fwd, k, self.params.time, v, 1.0, 1.0)
                for k, v in zip(strikes_tmp, vols_tmp)
            ]
            
            density_bump.append((prices[2] + prices[0] - 2 * prices[1]) / (bump * bump))
            probability_bump.append(1 + (prices[2] - prices[0]) / (2.0 * bump))

        return {
            "strikes": strikes.tolist(),
            "density": density,
            "density_bump": density_bump,
            "probability": probability,
            "probability_bump": probability_bump
        }

    def calculate_test3_density(self) -> Dict[str, List[float]]:
        strikes = np.linspace(0.3, 2.0, self.params.n)
        result = self.calculate_density_and_probability(strikes)
        return {
            "strikes": result["strikes"],
            "Tab_1": result["density"],
            "Tab_2": result["density_bump"]
        }

    def calculate_test4_probability(self) -> Dict[str, List[float]]:
        strikes = np.linspace(0.3, 2.0, self.params.n)
        result = self.calculate_density_and_probability(strikes)
        return {
            "strikes": result["strikes"],
            "Tab_1": result["probability"],
            "Tab_2": result["probability_bump"]
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
            
        result = test_functions[params.test]()
        print(json.dumps({"status": "success", "data": result, "error": None}))

    except Exception as e:
        print(json.dumps({"status": "error", "data": None, "error": str(e)}))

if __name__ == "__main__":
    main()