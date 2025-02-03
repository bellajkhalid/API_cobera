#!/usr/bin/env python3

import sys
import json
from dataclasses import dataclass
from typing import Dict, List, Union, Tuple
import numpy as np
from xsigmamodules.Util import (
    sabrPdeAnalytics,
    density_smoothing_type,
    blackScholes,
    bachelier,
    zabrMixtureAnalytics,
    zabrClassicalAnalytics,
    volatility_type,
    zabr_output_type,
    density_smoothing_type,
    zabrAnalytics,
    sabrPdeAnalyticsClassic,
)
from xsigmamodules.Math import normalDistribution
from xsigmamodules.util.numpy_support import numpyToXsigma

@dataclass
@dataclass
class ZabrParams:
    forward: float
    expiry: float
    alpha: float
    beta: float
    vol_of_vol: float
    rho: float
    shift: float
    gamma: float
    calibration_type: str
    dt: float = None  # Add dt attribute
    nd: float = None  # Add nd attribute
    

    @classmethod
    def from_argv(cls, argv: List[str]) -> 'ZabrParams':
        required_args = 9
        if len(argv) < required_args + 1:  # +1 for script name
            raise ValueError(
                "Required arguments: forward expiry alpha beta vol_of_vol rho shift gamma calibration_type"
            )
        
        param_names = ['forward', 'expiry', 'alpha', 'beta', 'vol_of_vol', 
                    'rho', 'shift', 'gamma', 'calibration_type']
        param_types = [float, float, float, float, float, float, float, float, str]
        
        try:
            params = {}
            for i, (name, type_) in enumerate(zip(param_names, param_types)):
                params[name] = type_(argv[i + 1])
            
            # Add dt and nd for PDE calibration
            if params['calibration_type'] == 'pde':
                if len(argv) < required_args + 3:  # +3 for dt and nd
                    raise ValueError(
                        "For PDE calibration, additional arguments are required: dt nd"
                    )
                params['dt'] = float(argv[required_args + 1])
                params['nd'] = float(argv[required_args + 2])
            
            return cls(**params)
        except ValueError as e:
            raise ValueError(f"Error parsing argument {param_names[i]}: {e}")
class ZabrCalibrator:
    def __init__(self, params: ZabrParams):
        self.params = params
        # Market data
        self.strikes_market = np.array([0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.1])
        self.vol_market = np.array([
            0.004653372, 0.00462834, 0.004641966, 0.004701461,
            0.004958582, 0.005357513, 0.008505604
        ])

    def calibrate_classical(self) -> Dict:
        """Perform ZABR Classical calibration."""
        try:
            N = 401
            # Initialize ZABR object
            obj_init = zabrClassicalAnalytics(
                self.params.expiry, self.params.forward, self.params.beta,
                self.params.shift, self.params.alpha, self.params.vol_of_vol,
                self.params.rho, self.params.gamma, True
            )
            
            # Create strike grid
            strikes = np.linspace(0.0, 0.12, N)
            strikes_replaced = np.array([
                strikes[np.abs(strikes - s).argmin()] 
                for s in self.strikes_market
            ])

            # Perform calibration
            obj_calibrated = zabrAnalytics.calibrate(
                obj_init, self.vol_market, strikes_replaced, N, strikes
            )

            # Calculate model values
            output = np.zeros(len(strikes))
            output_ = numpyToXsigma(output)
            strikes_ = numpyToXsigma(strikes)
            obj_calibrated.values(
                output_, strikes_, zabr_output_type.IMPLIED_VOLATILITY, False
            )

            return {
                "status": "success",
                "data": {
                    "strikes": strikes.tolist(),
                    "model_vols": output.tolist(),
                    "market_strikes": self.strikes_market.tolist(),
                    "market_vols": self.vol_market.tolist()
                }
            }

        except Exception as e:
            return {"status": "error", "data": None, "error": str(e)}

    def calibrate_pde(self) -> Dict:
        """Perform SABR PDE calibration."""
        try:
            if not hasattr(self.params, 'dt') or not hasattr(self.params, 'nd'):
                raise ValueError("dt and nd must be provided for PDE calibration")

            N = 401  # Number of grid points
            dt = self.params.dt
            nd = self.params.nd

            # Initialize PDE object
            obj_pde_init = sabrPdeAnalyticsClassic(
                self.params.expiry, self.params.forward, self.params.alpha,
                self.params.beta, self.params.vol_of_vol, self.params.rho,
                self.params.shift, N, dt, nd
            )

            # Perform calibration
            obj_pde = sabrPdeAnalyticsClassic.calibrate(
                self.vol_market, self.strikes_market, obj_pde_init
            )

            # Calculate implied volatilities
            vol_model = np.zeros_like(self.strikes_market)
            for i, k in enumerate(self.strikes_market):
                is_call = 1.0 if k > self.params.forward else -1.0
                p = obj_pde.price(k, True, density_smoothing_type.LINEAR)
                p = p - max(is_call * (self.params.forward - k), 0.0)
                if p > 0:
                    vol_model[i] = bachelier.implied_volatility(
                        self.params.forward, k, self.params.expiry,
                        p, 1.0, is_call
                    )

            return {
                "status": "success",
                "data": {
                    "strikes": self.strikes_market.tolist(),
                    "model_vols": vol_model.tolist(),
                    "market_vols": self.vol_market.tolist()
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "error": f"PDE calibration failed: {str(e)}"
            }
    def calibrate_mixture(self) -> Dict:
        """Perform ZABR Mixture calibration."""
        try:
            # Initialize mixture object
            obj_init = zabrMixtureAnalytics(
                self.params.expiry, self.params.forward,
                0.0132, 0.2, 1.25, 0.2, 0.0001,
                0.197, -0.444, 1, True
            )

            # Create strike grid
            N = 100
            strikes = np.array(
                zabrAnalytics.strike_grid(
                    self.params.expiry, self.params.forward,
                    N, self.strikes_market
                )
            )

            # Perform calibration
            obj_calibrated = zabrAnalytics.calibrate(
                obj_init, self.vol_market, self.strikes_market,
                N, strikes
            )

            # Calculate model values
            output = np.zeros(len(strikes))
            output_ = numpyToXsigma(output)
            strikes_ = numpyToXsigma(strikes)
            obj_calibrated.values(
                output_, strikes_, zabr_output_type.IMPLIED_VOLATILITY, False
            )

            return {
                "status": "success",
                "data": {
                    "strikes": strikes.tolist(),
                    "model_vols": output.tolist(),
                    "market_strikes": self.strikes_market.tolist(),
                    "market_vols": self.vol_market.tolist()
                }
            }

        except Exception as e:
            return {"status": "error", "data": None, "error": str(e)}

def main():
    try:
        params = ZabrParams.from_argv(sys.argv)
        calibrator = ZabrCalibrator(params)

        calibration_methods = {
            "classical": calibrator.calibrate_classical,
            "pde": calibrator.calibrate_pde,
            "mixture": calibrator.calibrate_mixture
        }

        if params.calibration_type not in calibration_methods:
            raise ValueError(
                f"Invalid calibration type: {params.calibration_type}. "
                f"Must be one of: {', '.join(calibration_methods.keys())}"
            )

        result = calibration_methods[params.calibration_type]()
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