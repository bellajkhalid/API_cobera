'use strict';

const utils = require('../utils/writer.js');
const HartmanWatsonDistribution = require('../service/HW_distribution.js');
const HjmCalibration = require('../service/hjm.js');

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
 * Controller for HJM Calibration endpoint
 */
module.exports.getHjmCalibration = async function getHjmCalibration(req, res, next) {
  console.log('Computing HJM calibration with params:', JSON.stringify(req.query, null, 2));
  try {
    await HjmCalibration.getHjmCalibration(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for Hartman-Watson Distribution endpoint
 */
module.exports.getHartmanWatsonDistribution = async function getHartmanWatsonDistribution(req, res, next) {
  console.log('Computing Hartman-Watson distribution with params:', JSON.stringify(req.query, null, 2));
  try {
    await HartmanWatsonDistribution.getHartmanWatsonDistribution(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};