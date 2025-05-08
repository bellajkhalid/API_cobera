import json
import sys
import time
import numpy as np
from itertools import chain
from xsigmamodules.Random import random_type
from xsigmamodules.Analytics import (
    calibrationIrTargetsConfiguration,
    correlationManager,
    calibrationHjmSettings,
    parameter_markovian_hjm_type,
    calibrationIrHjm,
    parameterMarkovianHjmId,
    parameterMarkovianHjm,
    dynamicInstructionId,
    dynamicInstructionIrMarkovianHjm,
    simulatedMarketDataIrId,
    correlationManagerId,
    dynamicInstructionIrId,
    measureId,
    measure,
    randomConfig,
    simulationManager,
    randomConfigId,
)
# Modified import to match Python 3.11 structure
from xsigmamodules.Market import (
    discountCurvePiecewiseConstant,  
    discountId,
    anyId,
    anyContainer,
    anyObject,
)
# Import irVolatilitySurface from another module if available
# For now, we'll try to import it from Analytics
from xsigmamodules.Analytics import irVolatilitySurface
# Continue with existing imports
from xsigmamodules.Util import dayCountConvention
from xsigmamodules.Vectorization import vector, matrix, tensor
from xsigmamodules.common import helper
from xsigmamodules.market import market_data
from xsigmamodules.simulation import simulation
from xsigmamodules.util.misc import xsigmaGetDataRoot, xsigmaGetTempDir
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma

def load_market_data(data_root: str) -> tuple:
    """Load all required market data files."""
    try:
        # Create discount_id and diffusion_id
        discount_id = discountId("LIBOR.3M.USD", "USD")
        diffusion_id = simulatedMarketDataIrId(discount_id)

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

        return target_config, discount_curve, ir_volatility_surface, correlation_mgr, convention, discount_id, diffusion_id
        
    except Exception as e:
        raise ConfigurationError(f"Error loading market data: {str(e)}")

def setup_calibration(diffusion_id, correlation_mgr: correlationManager) -> tuple:
    """Setup calibration parameters."""
    diffusion_ids = [diffusion_id]
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
                    diffusion_ids, correlation_mgr, convention, discount_id):
    """Process test case 2: Run simulation with market container."""
    print("PROGRESS: Starting simulation setup")
    mkt_data_obj = market_data.market_data(data_root)
    
    # Setup market container
    anyids = [anyId(discount_id)]
    anyobject = [anyObject(mkt_data_obj.discountCurve())]
    
    anyids.append(anyId(correlationManagerId()))
    anyobject.append(anyObject(correlation_mgr))
    
    anyids.append(anyId(parameterMarkovianHjmId(diffusion_ids[0])))
    anyobject.append(anyObject(parameter))
    
    anyids.append(anyId(dynamicInstructionIrId(diffusion_ids[0])))
    anyobject.append(anyObject(dynamicInstructionIrMarkovianHjm()))
    
    anyids.append(anyId(measureId()))
    anyobject.append(anyObject(measure(discount_id)))
    
    num_of_paths = 262144
    config = randomConfig(random_type.SOBOL_BROWNIAN_BRIDGE, 12765793, num_of_paths)
    
    anyids.append(anyId(randomConfigId()))
    anyobject.append(anyObject(config))
    
    market = anyContainer(anyids, anyobject)
    simulation_dates = helper.simulation_dates(valuation_date, "3M", 120)
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
    print("PROGRESS: Running simulation")
    sim.run_simulation(diffusion_ids, market, simulation_dates)
    
    # Process results
    x = list(sim.results.model_swaption_implied.keys())
    model_vols = np.array(list(sim.results.model_swaption_implied.values())).T * 10000
    market_vols = np.array(list(sim.results.market_swaption_implied.values())).T * 10000

    error = np.asarray(
        [model_vols[i] - market_vols[i] for i in range(len(model_vols))]
    )

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
    print("PROGRESS: Processing results")
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
        test = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        data_root = xsigmaGetDataRoot()
        
        # Load market data with additional IDs
        target_config, discount_curve, ir_volatility_surface, correlation_mgr, convention, discount_id, diffusion_id = load_market_data(data_root)
        valuation_date = discount_curve.valuation_date()
        
        # Setup calibration with diffusion_id
        diffusion_ids, correlation, calibration_settings_aad = setup_calibration(diffusion_id, correlation_mgr)
        
        # Create calibrator with target_config
        calibrator = calibrationIrHjm(valuation_date, target_config)
        
        # Calibrate with proper IDs
        parameter = calibrator.calibrate(
            parameterMarkovianHjmId(diffusion_id),
            calibration_settings_aad,
            discount_curve,
            ir_volatility_surface,
            correlation_mgr,
        )
        
        if test == 1:
            data = process_test_one(calibrator, parameter, valuation_date, convention, discount_curve)
        elif test == 2:
            data = process_test_two(parameter, valuation_date, target_config, data_root,
                                  diffusion_ids, correlation_mgr, convention, discount_id)
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