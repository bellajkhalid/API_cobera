import json
import sys
import numpy as np
from xsigmamodules.Analytics import (
    calibrationIrTargetsConfiguration,
    correlationManager,
    calibrationHjmSettings,
    parameter_markovian_hjm_type,
    calibrationIrHjm,
    diffusionIrMarkovianHjm,
)
from xsigmamodules.Market import discountCurvePiecewiseConstant, irVolatilitySurface
from xsigmamodules.Util import dayCountConvention
from xsigmamodules.common import helper
from xsigmamodules.market import market_data
from xsigmamodules.simulation import simulation
from xsigmamodules.util.misc import xsigmaGetDataRoot, xsigmaGetTempDir

class ConfigurationError(Exception):
    """Custom exception for configuration related errors."""
    pass

def load_market_data(data_root: str) -> tuple:
    """Load all required market data files."""
    try:
        target_config = calibrationIrTargetsConfiguration.read_from_json(
            f"{data_root}/Data/staticData/calibration_ir_targets_configuration.json"
        )
        discount_curve = discountCurvePiecewiseConstant.read_from_json(
            f"{data_root}/Data/marketData/discount_curve_piecewise_constant.json"
        )
        ir_volatility_surface = irVolatilitySurface.read_from_json(
            f"{data_root}/Data/marketData/ir_volatility_surface.json"
        )
        correlation_mgr = correlationManager.read_from_json(
            f"{data_root}/Data/marketData/correlation_manager.json"
        )
        convention = dayCountConvention.read_from_json(
            f"{data_root}/Data/staticData/day_count_convention_360.json"
        )
        
        return target_config, discount_curve, ir_volatility_surface, correlation_mgr, convention
    except Exception as e:
        raise ConfigurationError(f"Error loading market data: {str(e)}")

def setup_calibration(correlation_mgr: correlationManager) -> tuple:
    """Setup calibration parameters."""
    diffusion_ids = [correlation_mgr.id(0)]
    correlation = correlation_mgr.pair_correlation_matrix(diffusion_ids, diffusion_ids)
    
    volatility_bounds = [0.0001, 1]
    decay_bounds = [0.0001, 1.0]
    
    calibration_settings_aad = calibrationHjmSettings(
        correlation.rows(),
        volatility_bounds,
        decay_bounds,
        parameter_markovian_hjm_type.PICEWISE_CONSTANT,
        True,
        200,
        True,
        False,
        1.0,
    )
    
    return diffusion_ids, correlation, calibration_settings_aad

def process_test_one(calibrator, parameter, valuation_date, convention, discount_curve):
    """Process test case 1: Calculate CMS spread pricing."""
    expiry = parameter.volatilities_dates()
    expiry_fraction = helper.convert_dates_to_fraction(
        valuation_date,
        expiry,
        convention,
    )
    
    calls = [
        calibrator.cms_spread_pricing_experimental(
            valuation_date, exp_date, parameter, discount_curve
        )
        for exp_date in expiry
    ]
    
    response = {
        "status": "success",
        "data": {
            "expiry_fraction": expiry_fraction.tolist(),
            "calls": calls
        },
        "error": None
    }

    return response

def process_test_two(parameter, valuation_date, target_config, data_root, 
                     diffusion_ids, correlation_mgr, convention):
    """Process test case 2: Run simulation and return structured data."""
    mkt_data_obj = market_data.market_data(data_root)
    factors = [parameter.number_of_factors()]
    simulation_dates = helper.simulation_dates(valuation_date, "3M", 120)
    
    num_of_paths = 131072 * 2
    diffusions = [
        diffusionIrMarkovianHjm(simulation_dates, mkt_data_obj.discountCurve(), parameter)
    ]
    
    maturity = max(simulation_dates)
    
    sim = simulation.Simulation(
        mkt_data_obj,
        num_of_paths,
        target_config.frequency(),
        target_config.expiries(),
        target_config.cms_tenors(),
        target_config.coterminal(),
        maturity,
        simulation_dates,
    )
    
    sim.run_simulation(
        diffusion_ids, factors, diffusions, simulation_dates, correlation_mgr
    )
    
    # Extract data directly from sim.results
    x = list(sim.results.model_swaption_implied.keys())
    model_vols = np.array(list(sim.results.model_swaption_implied.values())).T * 10000
    market_vols = np.array(list(sim.results.market_swaption_implied.values())).T * 10000

    # Calculate error matrix
    error = np.asarray(
        [model_vols[i] - market_vols[i] for i in range(len(model_vols))]
    )

    # Restructure data with proper dictionary syntax
    volatility_data = {
        "data1": {"model": model_vols[0].tolist(), "market": market_vols[0].tolist()},
        "data2": {"model": model_vols[1].tolist(), "market": market_vols[1].tolist()},
        "data3": {"model": model_vols[2].tolist(), "market": market_vols[2].tolist()},
        "data4": {"model": model_vols[3].tolist(), "market": market_vols[3].tolist()}
    }

    error_data = {
        "data1": error[0].tolist(),
        "data2": error[1].tolist(),
        "data3": error[2].tolist(),
        "data4": error[3].tolist()
    }

    expiry = parameter.volatilities_dates()
    expiry_fraction = helper.convert_dates_to_fraction(
        valuation_date,
        expiry,
        convention,
    )
    
    response = {
        "status": "success",
        "data": {
            "NI_Volatility_Bps": volatility_data,
            "Error_Bps": error_data,
            "expiry_fraction": expiry_fraction.tolist(),
        },
        "error": None
    }

    return response

def main():
    try:
        # Get test parameter from command line arguments with default value
        test = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        data_root = xsigmaGetDataRoot()
        
        target_config, discount_curve, ir_volatility_surface, correlation_mgr, convention = load_market_data(data_root)
        valuation_date = discount_curve.valuation_date()
        
        diffusion_ids, correlation, calibration_settings_aad = setup_calibration(correlation_mgr)
        
        calibrator = calibrationIrHjm(valuation_date, discount_curve, target_config, convention)
        parameter = calibrator.calibrate(ir_volatility_surface, correlation, calibration_settings_aad)
        
        if test == 1:
            data = process_test_one(calibrator, parameter, valuation_date, convention, discount_curve)
        elif test == 2:
            data = process_test_two(parameter, valuation_date, target_config, data_root, 
                                  diffusion_ids, correlation_mgr, convention)
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