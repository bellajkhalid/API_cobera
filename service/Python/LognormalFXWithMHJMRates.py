import time
import json
import argparse
import numpy as np
from itertools import chain
from xsigmamodules.common import helper
from xsigmamodules.test import Testing
from xsigmamodules.market import market_data
from xsigmamodules.simulation import simulation
from xsigmamodules.util.misc import xsigmaGetDataRoot, xsigmaGetTempDir
from xsigmamodules.Analytics import (
    calibrationIrTargetsConfiguration,
    calibrationHjmSettings,
    calibrationIrHjm,
    correlationManager,
    correlationManagerId,
    dynamicInstructionId,
    dynamicInstructionIrId,
    dynamicInstructionIrMarkovianHjm,
    dynamicInstructionFxId,
    dynamicInstructionFxLognormal,
    simulatedMarketDataIrId,
    simulatedMarketDataFxId,
    simulationManager,
    parameter_markovian_hjm_type,
    parameterMarkovianHjmId,
    parameterMarkovianHjm,
    parameterLognormal,
    parameterLognormalId,
    measureId,
    measure,
    randomConfig,
    randomConfigId,
    lognormalFxWithMhjmIr,
)
from xsigmamodules.Market import (
    discountCurvePiecewiseConstant,
    irVolatilitySurface,
    discountCurve,
    discountId,
    fxForward,
    fxForwardId,
    anyId,
    anyContainer,
    anyObject,
)
from xsigmamodules.Util import dayCountConvention, blackScholes
from xsigmamodules.Random import random_type
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma
from xsigmamodules.Vectorization import vector, matrix, tensor

def parse_arguments():
    parser = argparse.ArgumentParser(description='LognormalFXWithMHJMRates Calculator')
    parser.add_argument('--num-paths', type=int, default=262144 * 2,
                      help='Number of simulation paths')
    parser.add_argument('--volatility', type=float, default=0.3,
                      help='Initial volatility parameter')
    return parser.parse_args()

def main():
    try:
        args = parse_arguments()
        num_paths = args.num_paths
        volatility = args.volatility

        XSIGMA_DATA_ROOT = xsigmaGetDataRoot()
        XSIGMA_TEST_ROOT = xsigmaGetTempDir()
        
        # Setup IDs
        dom_ir_id = discountId("LIBOR.3M.USD", "USD")
        diffusion_dom_id = simulatedMarketDataIrId(dom_ir_id)
        for_ir_id = discountId("LIBOR.3M.USD", "EUR")
        diffusion_for_id = simulatedMarketDataIrId(for_ir_id)
        fx_forward_id = fxForwardId(dom_ir_id, for_ir_id)
        diffusion_fx_id = simulatedMarketDataFxId(fx_forward_id)
        simulated_ids = [diffusion_dom_id, diffusion_for_id, diffusion_fx_id]
        
        # Setup instructions
        anyids = [anyId(dynamicInstructionIrId(diffusion_dom_id))]
        anyobject = [anyObject(dynamicInstructionIrMarkovianHjm())]
        anyids.append(anyId(dynamicInstructionIrId(diffusion_for_id)))
        anyobject.append(anyObject(dynamicInstructionIrMarkovianHjm()))
        anyids.append(anyId(dynamicInstructionFxId(diffusion_fx_id)))
        anyobject.append(anyObject(dynamicInstructionFxLognormal()))
        
        # Load parameters
        params_dom = parameterMarkovianHjm.read_from_json(
            XSIGMA_DATA_ROOT + "/Data/calibratedParameters/calibrated_mhjm_parameter_LIBOR.3M.USD_USD_3f.json"
        )
        anyids.append(anyId(parameterMarkovianHjmId(diffusion_dom_id)))
        anyobject.append(anyObject(params_dom))
        
        params_for = parameterMarkovianHjm.read_from_json(
            XSIGMA_DATA_ROOT + "/Data/calibratedParameters/calibrated_mhjm_parameter_LIBOR.3M.USD_EUR_2f.json"
        )
        anyids.append(anyId(parameterMarkovianHjmId(diffusion_for_id)))
        anyobject.append(anyObject(params_for))
        
        # Load market data
        discount_curve = discountCurvePiecewiseConstant.read_from_json(
            XSIGMA_DATA_ROOT + "/Data/marketData/discount_curve_piecewise_constant.json"
        )
        anyids.append(anyId(dom_ir_id))
        anyobject.append(anyObject(discount_curve))
        anyids.append(anyId(for_ir_id))
        anyobject.append(anyObject(discount_curve))
        
        # Setup FX forward
        valuation_date = discount_curve.valuation_date()
        fx_forward = fxForward(valuation_date, 1, discount_curve, discount_curve)
        anyids.append(anyId(fx_forward_id))
        anyobject.append(anyObject(fx_forward))
        
        # Setup correlation
        correlation_mgr = correlationManager.read_from_json(
            XSIGMA_DATA_ROOT + "/Data/marketData/correlation_manager.json"
        )
        anyids.append(anyId(correlationManagerId()))
        anyobject.append(anyObject(correlation_mgr))
        
        correlation = correlation_mgr.pair_correlation_matrix(simulated_ids, simulated_ids)
        valuation_date = correlation_mgr.valuation_date()
        calibrator = lognormalFxWithMhjmIr(valuation_date, correlation, params_dom, params_for)
        
        # Setup convention and dates
        convention = dayCountConvention.read_from_json(
            XSIGMA_DATA_ROOT + "/Data/staticData/day_count_convention_360.json"
        )
        calibration_dates = helper.simulation_dates(valuation_date, "3M", 120)
        expiry_fraction = helper.convert_dates_to_fraction(
            valuation_date, calibration_dates, convention
        )
        
        # Calculate market variance
        market_variance = []
        for i in range(0, len(calibration_dates)):
            market_variance.append(volatility * volatility * expiry_fraction[i])
            
        # Calibrate FX
        params_fx = calibrator.calibrate(calibration_dates, market_variance, convention)
        anyids.append(anyId(parameterLognormalId(diffusion_fx_id)))
        anyobject.append(anyObject(params_fx))
        
        # Setup measure and config
        anyids.append(anyId(measureId()))
        anyobject.append(anyObject(measure(dom_ir_id)))
        config = randomConfig(random_type.SOBOL_BROWNIAN_BRIDGE, 542897, num_paths)
        anyids.append(anyId(randomConfigId()))
        anyobject.append(anyObject(config))
        
        # Setup simulation
        market = anyContainer(anyids, anyobject)
        simulation_mgr = simulationManager(simulated_ids, market, calibration_dates)
        maturity = max(calibration_dates)
        
        # Setup curves
        diffusion_curve_domestic = simulation_mgr.discount_curve(diffusion_dom_id)
        diffusion_curve_foreign = simulation_mgr.discount_curve(diffusion_for_id)
        diffusion_fx = simulation_mgr.fx_forward(diffusion_fx_id)
        dis_for_curve = discount_curve
        dis_dom_curve = discount_curve
        
        # Initialize arrays
        mm_dom = np.zeros(num_paths)
        mm_for = np.zeros(num_paths)
        spot_fx_fwd = np.zeros(num_paths)
        log_discount_factor = np.zeros(num_paths)
        
        mm_dom_ = numpyToXsigma(mm_dom)
        mm_for_ = numpyToXsigma(mm_for)
        spot_fx_fwd_ = numpyToXsigma(spot_fx_fwd)
        log_discount_factor_ = numpyToXsigma(log_discount_factor)
        
        # Initialize results arrays
        results_mm_market = []
        results_df_market = []
        results_mm = []
        results_df = []
        model_vol = []
        market_vol = []
        model_stradle_vol = []
        fwds = []
        strikes = []
        
        df_for_maturity = dis_for_curve.df(valuation_date, maturity)
        simulation_mgr.states_initialize()
        
        # Run simulation
        for t in range(1, len(calibration_dates)):
            conditional_date = calibration_dates[t]
            simulation_mgr.propagate(t)
            
            # Calculate discounting
            diffusion_curve_domestic.discounting(mm_dom_, conditional_date)
            diffusion_curve_foreign.discounting(mm_for_, conditional_date)
            diffusion_curve_foreign.log_df(log_discount_factor_, conditional_date, maturity)
            diffusion_fx.forward(spot_fx_fwd_, conditional_date)
            
            # Convert back to numpy
            mm_dom = xsigmaToNumpy(mm_dom_)
            mm_for = xsigmaToNumpy(mm_for_)
            spot_fx_fwd = xsigmaToNumpy(spot_fx_fwd_)
            log_discount_factor = xsigmaToNumpy(log_discount_factor_)
            
            # Calculate market values
            df_for_market = dis_for_curve.df(valuation_date, conditional_date)
            df_dom_market = dis_dom_curve.df(valuation_date, conditional_date)
            results_mm_market.append(0.0)
            results_mm.append(np.average(mm_dom * spot_fx_fwd / mm_for) - 1.0)
            results_df_market.append(0.0)
            results_df.append(
                np.average(mm_dom * np.exp(log_discount_factor) * spot_fx_fwd) / df_for_maturity
                - 1
            )
            
            # Calculate forwards
            fwd = fx_forward.forward(conditional_date)
            strike = np.average(mm_dom * spot_fx_fwd) / np.average(mm_dom) - 1.0
            strikes.append(strike)
            fwds.append(fwd)
            
            # Calculate option values
            model_stradle_vol.append(np.average(mm_dom * (spot_fx_fwd - fwd)))
            fx_call_price = np.average(mm_dom * np.maximum(spot_fx_fwd - fwd, 0.0))
            fx_put_price = np.average(mm_dom * np.maximum(fwd - spot_fx_fwd, 0.0))
            
            # Calculate volatilities
            expiry_double = convention.fraction(valuation_date, conditional_date)
            model_vol.append(
                0.5
                * (
                    blackScholes.implied_volatility(
                        fwd, fwd, expiry_double, fx_call_price, df_dom_market, 1.0
                    )
                    + blackScholes.implied_volatility(
                        fwd, fwd, expiry_double, fx_put_price, df_dom_market, -1.0
                    )
                )
            )
            market_vol.append(np.sqrt(market_variance[t] / expiry_double))
            
        output = {
            "status": "success",
            "data": {
                "strikes": strikes,
                "model_volatility": model_vol,
                "market_volatility": market_vol,
                "results_money_market": results_mm,
                "results_discount_factors": results_df
            },
            "error": None
        }
        print(json.dumps(output))
        
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "data": None,
            "error": str(e)
        }))

if __name__ == "__main__":
    main()