#!/usr/bin/env python3

import sys
import json
import numpy as np
import common.sabrHelper as sabr
from xsigmamodules.Util import (
    zabrMixtureAnalytics,
    zabrClassicalAnalytics,
    sabrPdeAnalyticsClassic,
    zabr_output_type,
    density_smoothing_type,
    bachelier
)
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma

def create_model(model_class, values):
    """Create model instance based on model class and parameters."""
    if model_class == zabrClassicalAnalytics:
        return model_class(
            values["expiry"],
            values["forward"],
            values["beta"],
            values["shift"],
            values["alpha"],
            values["nu"],
            values["rho"],
            values["gamma"],
            values["use_vol_adjustement"]
        )
    elif model_class == zabrMixtureAnalytics:
        high_strike = max(
            values["high_strike"],
            values["smothing_factor"] + values["low_strike"]
        )
        return model_class(
            values["expiry"],
            values["forward"],
            values["alpha"],
            values["beta1"],
            values["beta2"],
            values["d"],
            values["vol_low"],
            values["nu"],
            values["rho"],
            values["gamma"],
            values["use_vol_adjustement"],
            high_strike,
            values["low_strike"],
            values["forward_cut_off"],
            values["smothing_factor"]
        )
    elif model_class == sabrPdeAnalyticsClassic:
        return model_class(
            values["expiry"],
            values["forward"],
            values["alpha"],
            values["beta"],
            values["nu"],
            values["rho"],
            values["shift"],
            values["N"],
            values["timesteps"],
            values["nd"]
        )

def compute_density(obj, x_values):
    """Compute density/implied volatility for given model and x values."""
    if isinstance(obj, sabrPdeAnalyticsClassic):
        implied_vol = np.zeros_like(x_values)
        forward = obj.forward()
        T = obj.expiry()
        for i, K in enumerate(x_values):
            is_call = 1.0 if K > forward else -1.0
            p = obj.price(K, True, density_smoothing_type.LINEAR)
            p = p - max(is_call * (forward - K), 0.0)
            vol = bachelier.implied_volatility(forward, K, T, p, 1.0, is_call)
            implied_vol[i] = vol
        return implied_vol
    else:
        implied_vol = np.zeros(len(x_values))
        implied_vol_ = numpyToXsigma(implied_vol)
        strikes_ = numpyToXsigma(x_values)
        obj.values(implied_vol_, strikes_, zabr_output_type.IMPLIED_VOLATILITY, False)
        return implied_vol

def create_volatility_dynamic(model_class, initial_values, current_values, x_values=None):
    """Calculate volatility data for both initial and current parameters."""
    # Create initial model
    obj_initial = create_model(model_class, initial_values)
    
    # Generate or use provided x values
    if x_values is None:
        if isinstance(obj_initial, sabrPdeAnalyticsClassic):
            x_initial = xsigmaToNumpy(obj_initial.strikes())
        else:
            x_initial = np.linspace(
                initial_values["forward"] * 0.5,
                initial_values["forward"] * 1.5,
                100
            )
    else:
        x_initial = x_values
    
    # Compute initial y values
    y_initial = compute_density(obj_initial, x_initial)
    
    # Create current model
    obj_current = create_model(model_class, current_values)
    
    # Generate x values for current model if needed
    if isinstance(obj_current, sabrPdeAnalyticsClassic):
        x_dynamic = xsigmaToNumpy(obj_current.strikes())
    else:
        x_dynamic = x_initial.copy()
    
    # Compute current y values
    y_dynamic = compute_density(obj_current, x_dynamic)
    
    return {
        "initial": {
            "strikes": x_initial.tolist(),
            "vols": y_initial.tolist()
        },
        "current": {
            "strikes": x_dynamic.tolist(),
            "vols": y_dynamic.tolist()
        }
    }

# Main script
if __name__ == "__main__":
    try:
        # Read parameters from stdin (passed as JSON string from server.js)
        params = json.loads(sys.argv[1])
        model_type = params.get("model_type", "classical")

        # Define initial values based on model type
        if model_type == "classical":
            initial_values = {
                "expiry": 10.0,
                "forward": 0.0325,
                "alpha": 0.0873,
                "beta": 0.7,
                "nu": 0.47,
                "rho": -0.48,
                "shift": 0.0,
                "gamma": 1.0,
                "use_vol_adjustement": True
            }
            model_class = zabrClassicalAnalytics
            x_values = np.linspace(0.0, 0.2, 100)

        elif model_type == "mixture":
            initial_values = {
                "expiry": 30,
                "forward": -0.0007,
                "alpha": 0.0132,
                "beta1": 0.2,
                "beta2": 1.25,
                "d": 0.2,
                "nu": 0.1978,
                "rho": -0.444,
                "gamma": 1.0,
                "use_vol_adjustement": True,
                "high_strike": 0.1,
                "vol_low": 0.0001,
                "low_strike": 0.02,
                "forward_cut_off": 0.02,
                "smothing_factor": 0.001
            }
            model_class = zabrMixtureAnalytics
            x_values = np.linspace(-0.15, 0.3, 401)

        elif model_type == "pde":
            initial_values = {
                "expiry": 30.0,
                "forward": 0.02,
                "alpha": 0.035,
                "beta": 0.25,
                "nu": 1.0,
                "rho": -0.1,
                "shift": 0.0,
                "N": 100,
                "timesteps": 5,
                "nd": 5
            }
            model_class = sabrPdeAnalyticsClassic
            x_values = np.linspace(0.0, 0.2, 100)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Update current parameters with values from the frontend
        current_params = {key: params.get(key, initial_values[key]) for key in initial_values}

        # Calculate plot data
        plot_data = create_volatility_dynamic(
            model_class,
            initial_values,
            current_params,
            x_values
        )

        # Output JSON data directly for server.js to parse
        print(json.dumps(plot_data))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }))
        sys.exit(1)