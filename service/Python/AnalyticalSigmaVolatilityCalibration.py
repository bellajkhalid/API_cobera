# AnalyticalSigmaVolatilityCalibration.py
import json
import numpy as np
import sys
from xsigmamodules.Util import analyticalSigmaVolatility, blackScholes
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma
from volatilityDensityModel import calculate_vols_and_density, generate_sample_data
def density(obj, strikes, spot, expiry):
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
    obj.asv_with_sensitivities(
        numpyToXsigma(strikes), *[numpyToXsigma(arr) for arr in arrays.values()], False
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
    density_data = {
        "strikes": strikes.tolist(),
        "density": density
    }
    return density_data


def main():
    try:
        # Parse command line arguments directly
        if len(sys.argv) < 10:
            raise ValueError("Insufficient arguments provided")

        num_points = int(sys.argv[1])
        spot = float(sys.argv[2])
        expiry = float(sys.argv[3])
        risk_free_rate = float(sys.argv[4])
        dividend_yield = float(sys.argv[5])
        beta = float(sys.argv[6])
        rho = float(sys.argv[7])
        volvol = float(sys.argv[8])
        computationType = sys.argv[9]

        # Generate sample data
        calibration_strikes, bid_values, ask_values, mid_values = generate_sample_data()

        # Create and calibrate the analyticalSigmaVolatility object
        obj = analyticalSigmaVolatility(
            expiry, spot, spot, 0.2, volvol, beta, rho, 
            risk_free_rate, dividend_yield, 0.00006
        )
        obj.calibrate(numpyToXsigma(mid_values), numpyToXsigma(calibration_strikes))

        # Calculate volatilities
        vols = np.zeros(num_points)
        strikes = np.linspace(1800, 2700, num_points)
        obj.asv(numpyToXsigma(vols), numpyToXsigma(strikes))

        volatility_smile = {
            "calibration_strikes": calibration_strikes.tolist(),
            "bid_values": bid_values.tolist(),
            "ask_values": ask_values.tolist(),
            "mid_values": mid_values.tolist(),
            "strikes": strikes.tolist(),
            "vols": vols.tolist()
        }

        response = {
            "status": "success",
            "data": None,
            "error": None,
            "computationType": computationType
        }

        if computationType == "volatility":
            response["data"] = volatility_smile
        elif computationType == "density":
            density_data = density(obj, strikes, spot, expiry)
            response["data"] = density_data
        elif computationType == "interactive_model":
            response["data"] = density(obj, strikes, spot, expiry)
        else:
            response["status"] = "error"
            response["error"] = f"Invalid computation type: {computationType}"

        print(json.dumps(response))

    except Exception as e:
        error_response = {
            "status": "error",
            "data": None,
            "error": str(e),
            "computationType": computationType if 'computationType' in locals() else None
        }
        print(json.dumps(error_response))

if __name__ == "__main__":
    main()