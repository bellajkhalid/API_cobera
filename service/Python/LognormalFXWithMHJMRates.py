import json
import sys
import numpy as np
from xsigmamodules.Analytics import (
    correlationManager,
    parameterMarkovianHjm,
    lognormalFxWithMhjmIr,
    diffusionIrMarkovianHjm,
    diffusionFxLognormal,
    randomConfig,
    changeOfMeasure,
    simulationManager
)
from xsigmamodules.Market import fxSpot
from xsigmamodules.Util import dayCountConvention
from xsigmamodules.common import helper
from xsigmamodules.market import market_data
from xsigmamodules.Random import random_type
from xsigmamodules.util.numpy_support import numpyToXsigma, xsigmaToNumpy
from xsigmamodules.util.misc import xsigmaGetDataRoot

def process_test_one(params, correlation_mgr, convention, correlation):
    """Calculate FX volatility calibration."""
    valuation_date = correlation_mgr.valuation_date()
    calibrator = lognormalFxWithMhjmIr(valuation_date, correlation, params, params)
    
    # Create calibration dates and calculate expiry fraction
    calibration_dates = helper.simulation_dates(valuation_date, "3M", 120)
    expiry_fraction = helper.convert_dates_to_fraction(
        valuation_date,
        calibration_dates,
        convention,
    )
    
    # Calculate market variance
    volatility = 0.2
    market_variance = [volatility * volatility * t for t in expiry_fraction]
    
    # Calibrate parameters
    params_fx = calibrator.calibrate(calibration_dates, market_variance, convention)
    
    # Convert volatilities to numpy array then to list
    volatilities = xsigmaToNumpy(params_fx.volatilities())
    
    response = {
        "status": "success",
        "data": {
            "expiry_fraction": expiry_fraction.tolist(),
            "volatilities": volatilities.tolist()
        },
        "error": None
    }
    
    return response

def process_test_two(params, correlation_mgr, convention, diffusion_ids):
    """Run simulation and return money market account results."""
    try:
        valuation_date = correlation_mgr.valuation_date()
        mkt_data_obj = market_data.market_data(xsigmaGetDataRoot())
        
        # Setup simulation parameters
        simulation_dates = helper.simulation_dates(valuation_date, "3M", 120)
        maturity = max(simulation_dates)
        num_of_paths = 1000
        factors = 3
        
        # Create FX parameters
        calibrator = lognormalFxWithMhjmIr(
            valuation_date, 
            correlation_mgr.pair_correlation_matrix(diffusion_ids, diffusion_ids),
            params, 
            params
        )
        
        # Calculate market variance for FX calibration
        calibration_dates = simulation_dates
        expiry_fraction = helper.convert_dates_to_fraction(
            valuation_date,
            calibration_dates,
            convention,
        )
        volatility = 0.2
        market_variance = [volatility * volatility * t for t in expiry_fraction]
        params_fx = calibrator.calibrate(calibration_dates, market_variance, convention)
        
        # Setup diffusions
        diffusions = [
            diffusionIrMarkovianHjm(simulation_dates, mkt_data_obj.discountCurve(), params),
            diffusionIrMarkovianHjm(simulation_dates, mkt_data_obj.discountCurve(), params),
            diffusionFxLognormal(
                simulation_dates,
                fxSpot(valuation_date, 1.0),
                mkt_data_obj.discountCurve(),
                mkt_data_obj.discountCurve(),
                params_fx,
            )
        ]
        
        # Setup simulation configuration
        config = randomConfig(
            random_type.SOBOL_BROWNIAN_BRIDGE,
            12765793,
            num_of_paths,
            len(simulation_dates),
            factors
        )
        
        # Setup change of measures
        change_of_measures = [changeOfMeasure(), changeOfMeasure(), changeOfMeasure()]
        
        # Create simulation manager
        simulation_mgr = simulationManager(
            diffusions,
            change_of_measures,
            correlation_mgr.pair_correlation_matrix(diffusion_ids, diffusion_ids),
            config,
            simulation_dates,
        )
        
        # Initialize arrays for results
        mm_dom = np.zeros(num_of_paths)
        mm_dom_ = numpyToXsigma(mm_dom)
        results_mm = []
        
        # Run simulation
        simulation_mgr.states_initialize()
        # Fix: Use the first diffusion from the diffusions list
        diffusion_curve_domestic = diffusions[0].diffusion_discount_curve(simulation_mgr.data(0))
        
        for t in range(1, len(simulation_dates)):
            simulation_mgr.propagate(t)
            conditional_date = simulation_dates[t]
            diffusion_curve_domestic.discounting(mm_dom_, conditional_date)
            results_mm.append(float(np.average(mm_dom)))
        
        response = {
            "status": "success",
            "data": {
                "time_indices": list(range(len(results_mm))),
                "money_market": results_mm
            },
            "error": None
        }
        
        return response
        
    except Exception as e:
        raise Exception(f"Error in process_test_two: {str(e)}")

def main():
    try:
        test = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        data_root = xsigmaGetDataRoot()
        
        # Load base data
        params = parameterMarkovianHjm.read_from_json(
            f"{data_root}/Data/calibratedParameters/calibrated_mhjm_parameter_LIBOR.3M.USD_GBP_1f.json"
        )
        correlation_mgr = correlationManager.read_from_json(
            f"{data_root}/Data/marketData/correlation_manager.json"
        )
        convention = dayCountConvention.read_from_json(
            f"{data_root}/Data/staticData/day_count_convention_360.json"
        )
        
        diffusion_ids = [correlation_mgr.id(0)]
        correlation = correlation_mgr.pair_correlation_matrix(diffusion_ids, diffusion_ids)
        
        if test == 1:
            data = process_test_one(params, correlation_mgr, convention, correlation)
        elif test == 2:
            data = process_test_two(params, correlation_mgr, convention, diffusion_ids)
        else:
            raise ValueError(f"Invalid test value: {test}. Must be 1 or 2.")
        
        print(json.dumps(data))
        
    except Exception as e:
        error_response = {
            "status": "error",
            "data": None,
            "error": str(e)
        }
        print(json.dumps(error_response))
        
if __name__ == "__main__":
    main()