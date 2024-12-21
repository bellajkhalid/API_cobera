
import sys
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from xsigmamodules.Util import (
    sabrPdeAnalytics,
    density_smoothing_type,
    blackScholes,
    bachelier,
    dayCountConvention,
    day_count_convention_type,
    datetimeHelper,
    zabrMixtureAnalytics,
    sabrAnalytics,
    zabrClassicalAnalytics,
    volatility_type,
    zabr_output_type,
    density_smoothing_type,
    zabrAnalytics,
    sabrPdeAnalyticsClassic,
)
from xsigmamodules.Math import normalDistribution
from xsigmamodules.Market import discountCurvePiecewiseConstant, irVolatilitySurface
from xsigmamodules.util.misc import xsigmaGetDataRoot, xsigmaGetTempDir
from xsigmamodules.util.numpy_support import numpyToXsigma

@dataclass
class CalibrationParams:
    n: int
    forward: float = 0.02
    expiry: float = 30
    alpha: float = 0.00955
    beta: float = 0.956
    vol_of_vol: float = 0.373
    rho: float = -0.749
    shift: float = 0.0
    gamma: float = 1.0
    
    @classmethod
    def from_argv(cls, argv: List[str]) -> 'CalibrationParams':
        if len(argv) < 2:
            raise ValueError(
                "Required arguments: test_number [forward expiry alpha beta vol_of_vol rho shift gamma]"
            )
        
        try:
            return cls(
                n=int(argv[1]),
                forward=float(argv[2]) if len(argv) > 2 else 0.02,
                expiry=float(argv[3]) if len(argv) > 3 else 30,
                alpha=float(argv[4]) if len(argv) > 4 else 0.00955,
                beta=float(argv[5]) if len(argv) > 5 else 0.956,
                vol_of_vol=float(argv[6]) if len(argv) > 6 else 0.373,
                rho=float(argv[7]) if len(argv) > 7 else -0.749,
                shift=float(argv[8]) if len(argv) > 8 else 0.0,
                gamma=float(argv[9]) if len(argv) > 9 else 1.0
            )
        except ValueError as e:
            raise ValueError(f"Error parsing arguments: {e}")

class VolatilityCalibrator:
    def __init__(self, params: CalibrationParams):
        self.params = params
        self._initialize_market_data()
        
    def _initialize_market_data(self):
        """Initialize market data and parameters."""
        self.strikes = np.array([0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.1])
        self.vol_mkt = np.array([
            0.004653372, 0.00462834, 0.004641966, 0.004701461,
            0.004958582, 0.005357513, 0.008505604
        ])

    def calculate_test1_volatility(self) -> Dict[str, Any]:
        """ZABR Classical Calibration."""
        try:
            N = 401
            obj_init_1 = zabrClassicalAnalytics(True)  # Just pass use_log_normal flag
            obj_init_1.init(
                self.params.expiry,
                self.params.forward,
                self.params.beta,
                self.params.shift,
                self.params.alpha,
                self.params.vol_of_vol,
                self.params.rho,
                self.params.gamma
            )
            
            strikes = np.linspace(0., 0.12, N)
            strikes_replaced = np.array([strikes[np.abs(strikes - s).argmin()] for s in self.strikes])
            
            # Calibrate ZABR
            obj2 = zabrAnalytics.calibrate(obj_init_1, self.vol_mkt, strikes_replaced, N, strikes)
            
            # Calculate implied volatilities
            output = np.zeros(len(strikes))
            output_ = numpyToXsigma(output)
            strikes2_ = numpyToXsigma(strikes)
            obj2.values(output_, strikes2_, zabr_output_type.IMPLIED_VOLATILITY, False)
            
            return {
                "zabr_results": {
                    "strikes": strikes.tolist(),
                    "implied_volatilities": output.tolist(),
                    "market_strikes": self.strikes.tolist(),
                    "market_vols": self.vol_mkt.tolist()
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Error in ZABR calibration: {str(e)}")

    def calculate_test2_volatility(self) -> Dict[str, Any]:
        """SABR PDE calibration."""
        try:
            N = 401
            dt = 5
            nd = 3.5
            
            # Create SABR PDE object with initialization parameters
            obj_pde_init = sabrPdeAnalyticsClassic(N, dt, nd)
            obj_pde_init.init(
                self.params.expiry,
                self.params.forward,
                self.params.alpha,
                self.params.beta,
                self.params.vol_of_vol,
                self.params.rho,
                self.params.shift
            )
            
            obj_pde = sabrPdeAnalyticsClassic.calibrate(
                self.vol_mkt,
                self.strikes,
                obj_pde_init
            )
            
            vol_model = np.zeros_like(self.strikes)
            prices = []
            
            for i, k in enumerate(self.strikes):
                is_call = 1.0 if k > self.params.forward else -1.0
                p = obj_pde.price(k, True, density_smoothing_type.LINEAR)
                prices.append(p)
                p_adjusted = p - max(is_call*(self.params.forward-k), 0.)
                if p_adjusted > 0:
                    vol_model[i] = bachelier.implied_volatility(
                        self.params.forward, k, self.params.expiry, p_adjusted, 1.0, is_call
                    )
            
            return {
                "sabr_pde_results": {
                    "strikes": self.strikes.tolist(),
                    "vol_model": vol_model.tolist(),
                    "market_vols": self.vol_mkt.tolist(),
                    "prices": prices
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Error in SABR PDE calibration: {str(e)}")

    def calculate_test3_volatility(self) -> Dict[str, Any]:
        """Mixture calibration."""
        try:
            # Create mixture analytics object with initialization parameters
            obj_init = zabrMixtureAnalytics(True)  # Just pass use_log_normal flag
            obj_init.init(
                self.params.expiry,
                self.params.forward,
                0.0132, 0.2, 1.25, 0.2, 0.0001, 0.197, -0.444, 1
            )
            
            N = 100
            strikes2 = np.array(zabrAnalytics.strike_grid(
                self.params.expiry,
                self.params.forward,
                N,
                self.strikes
            ))
            
            obj = zabrAnalytics.calibrate(obj_init, self.vol_mkt, self.strikes, N, strikes2)
            
            output = np.zeros(len(strikes2))
            output_ = numpyToXsigma(output)
            strikes2_ = numpyToXsigma(strikes2)
            
            obj.values(output_, strikes2_, zabr_output_type.IMPLIED_VOLATILITY, False)
            
            return {
                "mixture_results": {
                    "strikes": strikes2.tolist(),
                    "implied_volatilities": output.tolist(),
                    "market_strikes": self.strikes.tolist(),
                    "market_vols": self.vol_mkt.tolist()
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Error in mixture calibration: {str(e)}")

def main() -> None:
    try:
        params = CalibrationParams.from_argv(sys.argv)
        calculator = VolatilityCalibrator(params)
        
        test_functions = {
            1: calculator.calculate_test1_volatility,
            2: calculator.calculate_test2_volatility,
            3: calculator.calculate_test3_volatility
        }
        
        if params.n not in test_functions:
            raise ValueError(f"Invalid test case: {params.n}. Must be between 1 and 3.")
            
        data = test_functions[params.n]()
        response = {"status": "success", "data": data, "error": None}

    except Exception as e:
        response = {"status": "error", "data": None, "error": str(e)}

    print(json.dumps(response, default=str))

if __name__ == "__main__":
    main()