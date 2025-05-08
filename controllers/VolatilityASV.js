'use strict';

const utils = require('../utils/writer.js');
const AnalyticalSigmaVolatilityCalibration = require('../service/AnalyticalSigmaVolatilityCalibration.js');
const AnalyticalSigmaVolatility = require('../service/AnalyticalSigmaVolatility.js');
const VolatilityAsv = require('../service/volatility_asv.js');

/**
 * Generic error handler for all controller methods
 * @param {Error} error - The error object
 * @param {Object} res - Express response object
 * @returns {Object} JSON response with error details
 */
const handleError = (error, res) => {
  console.error('Controller error:', error);
  const status = error.status || 500;
  const errorResponse = {
    status: 'error',
    error: error.message || 'Internal Server Error',
    errorType: error.name || 'GeneralError',
    timestamp: new Date().toISOString()
  };
  
  // Include detailed error info in development mode
  if (process.env.NODE_ENV === 'development') {
    errorResponse.details = {
      stack: error.stack,
      code: error.code,
      stderr: error.stderr
    };
  }
  
  return utils.writeJson(res, errorResponse, status);
};

/**
 * Controller for ASV volatility GET endpoint
 */
module.exports.getVolatilityAsv = async function getVolatilityAsv(req, res, next) {
  console.log('Computing ASV volatility with params:', JSON.stringify(req.query, null, 2));
  try {
    await VolatilityAsv.getVolatilityData_asv(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for ASV volatility POST endpoint
 */
module.exports.postVolatilityAsv = async function postVolatilityAsv(req, res, next) {
  console.log('Computing ASV volatility with body params:', JSON.stringify(req.body, null, 2));
  try {
    await VolatilityAsv.getVolatilityData_asv({ query: req.body }, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for Analytical Sigma Volatility GET endpoint
 */
module.exports.getAnalyticalSigmaVolatility = async function getAnalyticalSigmaVolatility(req, res, next) {
  console.log('Computing analytical sigma volatility with params:', JSON.stringify(req.query, null, 2));
  try {
    await AnalyticalSigmaVolatility.getAnalyticalSigmaVolatility(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for Analytical Sigma Volatility Calibration POST endpoint
 * This controller handles the POST /AnalyticalSigmaVolatilityCalibration route
 * It performs volatility model calibration and computes volatility surfaces or density functions
 */
module.exports.volatility_densityPOST = async function volatility_densityPOST(req, res, next) {
  console.log('Processing AnalyticalSigmaVolatilityCalibration request with params:', 
    JSON.stringify(req.body, null, 2));
  
  try {
    // The actual validation is performed in the service layer and middleware
    await AnalyticalSigmaVolatilityCalibration.volatility_densityPOST(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};