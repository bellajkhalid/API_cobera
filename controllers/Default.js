'use strict';

const utils = require('../utils/writer.js');
const AnalyticalSigmaVolatilityCalibration = require('../service/AnalyticalSigmaVolatilityCalibration.js');
const AnalyticalSigmaVolatility = require('../service/AnalyticalSigmaVolatility.js');
const HartmanWatsonDistribution = require('../service/HW_distribution.js');
const HjmCalibration = require('../service/hjm.js');
const MHJMRates = require('../service/LognormalFXWithMHJMRate.js');

// [Previous exports remain the same]

module.exports.LognormalFXWithMHJMRates = async function LognormalFXWithMHJMRates(req, res, next) {
  console.log('Computing HJM calibration with params:', JSON.stringify(req.query, null, 2));
  try {
    const response = await MHJMRates.LognormalFXWithMHJMRates(req, res);
    // Note: The response is handled within the service function
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    return utils.writeJson(res, errorResponse, status);
  }
};
// [Previous exports remain the same]

module.exports.getHjmCalibration = async function getHjmCalibration(req, res, next) {
  console.log('Computing HJM calibration with params:', JSON.stringify(req.query, null, 2));
  try {
    const response = await HjmCalibration.getHjmCalibration(req, res);
    // Note: The response is handled within the service function
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    return utils.writeJson(res, errorResponse, status);
  }
};
module.exports.getHartmanWatsonDistribution = async function getHartmanWatsonDistribution(req, res, next) {
  console.log('Computing Hartman-Watson distribution with params:', JSON.stringify(req.query, null, 2));
  try {
    const response = await HartmanWatsonDistribution.getHartmanWatsonDistribution(req, res);
    // Note: The response is handled within the service function
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    return utils.writeJson(res, errorResponse, status);
  }
};
// Add this new function to the existing exports
module.exports.getAnalyticalSigmaVolatility = async function getAnalyticalSigmaVolatility(req, res, next) {
  console.log('Computing analytical sigma volatility with params:', JSON.stringify(req.query, null, 2));
  try {
    const response = await AnalyticalSigmaVolatility.getAnalyticalSigmaVolatility(req, res);
    // Note: The response is handled within the service function
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    return utils.writeJson(res, errorResponse, status);
  }
};
/**
 * Controller for compute POST endpoint
 */
module.exports.volatility_densityPOST = async function computePOST(req, res, next) {
  console.log('Computing using body:', JSON.stringify(req.body, null, 2));
  try {
    const response = await AnalyticalSigmaVolatilityCalibration.compute_volatility_density_POST(req.body);
    utils.writeJson(res, response);
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    utils.writeJson(res, errorResponse, status);
  }
};
/**
 * Controller for compute POST endpoint
 */
module.exports.updateVolatilityData_svi = async (req, res, next) => {
  try {
    const response = await AnalyticalSigmaVolatilityCalibration.getVolatilityData_svi(req, res);
    // Remove the res.json() call from here
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    return utils.writeJson(res, errorResponse, status);
  }
};

module.exports.updateVolatilityData_asv = async (req, res, next) => {
  try {
    const response = await AnalyticalSigmaVolatilityCalibration.getVolatilityData_asv(req, res);
    // Remove the res.json() call from here
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    return utils.writeJson(res, errorResponse, status);
  }
};
/**
 * Controller for interactive_model POST endpoint
 */
/**
 * Controller for test GET endpoint
 */
module.exports.testGET = async function testGET(req, res, next) {
  try {
    const response = await Default.testGET();
    utils.writeJson(res, response);
  } catch (error) {
    console.error('Controller error:', error);
    const status = error.status || 500;
    const errorResponse = {
      error: error.message || 'Internal Server Error',
      status: status,
      timestamp: new Date().toISOString()
    };
    utils.writeJson(res, errorResponse, status);
  }
};
