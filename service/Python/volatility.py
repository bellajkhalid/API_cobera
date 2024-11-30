import json
import sys
from volatilityDensityModel import calculate_vols_and_density

def volatility_smile_and_density(initial_values, current_params, model_type="asv", legacy_parametrisation=False):
    # Calculate for initial values
    initial_strikes, initial_vols, initial_density = calculate_vols_and_density(
        initial_values["fwd"], initial_values, model_type, legacy_parametrisation
    )

    # Calculate for current parameters
    current_strikes, current_vols, current_density = calculate_vols_and_density(
        initial_values["fwd"], current_params, model_type, legacy_parametrisation
    )

    # Convert numpy arrays to lists to make them JSON serializable
    return {
        "initial": {
            "strikes": initial_strikes.tolist(),
            "vols": initial_vols.tolist(),
            "density": initial_density.tolist(),
        },
        "current": {
            "strikes": current_strikes.tolist(),
            "vols": current_vols.tolist(),
            "density": current_density.tolist(),
        },
    }

# Main script
if __name__ == "__main__":
    # Read parameters from stdin (passed as JSON string from server.js)
    params = json.loads(sys.argv[1])

    # Define initial values
    initial_values = {
        "fwd": 1.0,
        "time": 0.333,
        "ctrl_p": 0.2,
        "ctrl_c": 0.2,
        "atm": 0.1929,
        "skew": 0.02268,
        "smile": 0.003,
        "put": 0.0384,
        "call": 0.0001
    }

    # Update current parameters with values from the frontend
    current_params = {key: params.get(key, initial_values[key]) for key in initial_values}

    # Calculate plot data
    plot_data = volatility_smile_and_density(initial_values, current_params)

    # Output JSON data directly for server.js to parse
    print(json.dumps(plot_data))