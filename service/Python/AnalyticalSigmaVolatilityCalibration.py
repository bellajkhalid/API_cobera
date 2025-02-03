#!/usr/bin/env python3

import sys
import json
import numpy as np
from xsigmamodules.Util import (
    blackScholes,
    sigmaVolatilityInspired,
    volatility_type
)
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma
from xsigmamodules.Market import volatilityModelExtendedSvi
from xsigmamodules.Math import (
    solverOptionsCeres,
    solverOptionsLm,
    solverOptionsNlopt,
    nlopt_algo_name
)
from common.volatilityDensityModel import (
    create_interactive_model,
    plot_density,
    generate_sample_data,
    plot_volatility_smile
)

def density_new(obj, strikes, spot, expiry):
    n = len(strikes)
    arrays = {
        "vols": np.zeros(n),
        "atm_sensitivity": np.zeros(n),
        "skew_sensitivity": np.zeros(n),
        "smile_sensitivity": np.zeros(n),
        "put_sensitivity": np.zeros(n),
        "call_sensitivity": np.zeros(n),
        "strike_sensitivity": np.zeros(n),
        "ref_sensitivity": np.zeros(n),
        "atm2_sensitivity": np.zeros(n),
        "ref2_sensitivity": np.zeros(n),
        "strike2_sensitivity": np.zeros(n),
    }

    obj.sensitivities(
        expiry, numpyToXsigma(strikes), *[numpyToXsigma(arr) for arr in arrays.values()]
    )

    density = [
        blackScholes.density(spot, strike, expiry, vol, strike_sens, strike2_sens)
        for strike, vol, strike_sens, strike2_sens in zip(
            strikes,
            arrays["vols"],
            arrays["strike_sensitivity"],
            arrays["strike2_sensitivity"],
        )
    ]

    return density


def calculate_vols_and_density(params, computation_type):
    try:
        calibration_strikes, bid_values, ask_values, mid_values = generate_sample_data()
        
        initial_guess_obj = volatilityModelExtendedSvi(
            params['spot'], 0.2, params['volvol'], params['beta'], 
            params['rho'], params['r'], params['q'], 0.00006
        )

        # Calibrate with different solvers
        options_ceres = solverOptionsCeres(500, 1e-14, 1e-14, 1e-14)
        calibrated_obj_ceres = volatilityModelExtendedSvi.calibrate(
            numpyToXsigma(calibration_strikes),
            numpyToXsigma(mid_values),
            params['spot'],
            params['expiry'],
            options_ceres,
            1,
            1,
            initial_guess_obj
        )

        strikes = np.linspace(1800, 2700, params['n'])

        if computation_type == "volatility_asv":
            vols = np.zeros(params['n'])
            calibrated_obj_ceres.implied_volatility(
                numpyToXsigma(vols),
                numpyToXsigma(strikes),
                1.0,
                params['expiry'],
                volatility_type.LOG_NORMAL
            )
            
            return {
                "status": "success",
                "computationType": "volatility_asv",
                "data": {
                    "calibration_strikes": calibration_strikes.tolist(),
                    "bid_values": bid_values.tolist(),
                    "ask_values": ask_values.tolist(),
                    "mid_values": mid_values.tolist(),
                    "strikes": strikes.tolist(),
                    "vols": vols.tolist()
                }
            }

        elif computation_type == "density":
            density=density_new(calibrated_obj_ceres, strikes, params['spot'], params['expiry'])
            return {
                "status": "success",
                "computationType": "density",
                "data": {
                    "strikes": strikes.tolist(),
                    "density": density
                }
            }

        elif computation_type == "volatility_svi":
            initial_values = {
                "fwd": 1.0,
                "time": 0.333,
                "b": 0.1,
                "m": 0.01,
                "sigma": 0.4
            }
            
            obj_svi = sigmaVolatilityInspired(
                params['spot'],
                initial_values["b"],
                initial_values["m"],
                initial_values["sigma"]
            )
            obj_svi.calibrate(
                numpyToXsigma(mid_values),
                numpyToXsigma(calibration_strikes)
            )
            
            vols = np.zeros(params['n'])
            obj_svi.svi(numpyToXsigma(vols), numpyToXsigma(strikes))
            
            return {
                "status": "success",
                "computationType": "volatility_svi",
                "data": {
                    "calibration_strikes": calibration_strikes.tolist(),
                    "bid_values": bid_values.tolist(),
                    "ask_values": ask_values.tolist(),
                    "mid_values": mid_values.tolist(),
                    "strikes": strikes.tolist(),
                    "vols": vols.tolist()
                }
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    try:
        if len(sys.argv) < 10:
            raise ValueError("Insufficient arguments")

        params = {
            'n': int(sys.argv[1]),
            'spot': float(sys.argv[2]),
            'expiry': float(sys.argv[3]),
            'r': float(sys.argv[4]),
            'q': float(sys.argv[5]),
            'beta': float(sys.argv[6]),
            'rho': float(sys.argv[7]),
            'volvol': float(sys.argv[8])
        }
        computation_type = sys.argv[9]

        result = calculate_vols_and_density(params, computation_type)
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()