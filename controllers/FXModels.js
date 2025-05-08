'use strict';

const utils = require('../utils/writer.js');
const MHJMRates = require('../service/LognormalFXWithMHJMRate.js');

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
 * Controller for MHJM Rates endpoint
 */
module.exports.LognormalFXWithMHJMRates = async function LognormalFXWithMHJMRates(req, res, next) {
  console.log('Computing HJM calibration with params:', JSON.stringify(req.query, null, 2));
  try {
    await MHJMRates.LognormalFXWithMHJMRates(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};