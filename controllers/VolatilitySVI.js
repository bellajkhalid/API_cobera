'use strict';

const utils = require('../utils/writer.js');
const VolatilitySvi = require('../service/volatility_svi.js');

/**
 * Generic error handler for all controller methods
 */
const handleError = (error, res) => {
  console.error('Controller error:', error);
  const status = error.status || 500;
  const errorResponse = {
    status: 'error',
    error: error.message || 'Internal Server Error',
    timestamp: new Date().toISOString()
  };
  return utils.writeJson(res, errorResponse, status);
};

/**
 * Controller for SVI volatility GET endpoint
 */
module.exports.getVolatilitySvi = async function getVolatilitySvi(req, res, next) {
  console.log('Computing SVI volatility with params:', JSON.stringify(req.query, null, 2));
  try {
    await VolatilitySvi.getVolatilityDataSvi(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for SVI volatility POST endpoint
 */
module.exports.postVolatilitySvi = async function postVolatilitySvi(req, res, next) {
  console.log('Computing SVI volatility with body params:', JSON.stringify(req.body, null, 2));
  try {
    await VolatilitySvi.getVolatilityDataSvi({ query: req.body }, res);
  } catch (error) {
    return handleError(error, res);
  }
};