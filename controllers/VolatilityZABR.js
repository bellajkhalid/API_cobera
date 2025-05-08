'use strict';

const utils = require('../utils/writer.js');
const ZabrCalibration = require('../service/zabr_calibration.js');
const ZabrAnalytics = require('../service/zabr_analytics.js');

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
 * Controller for Classical ZABR model endpoint
 */
module.exports.getVolatilityDataClassical = async function getVolatilityDataClassical(req, res, next) {
  console.log('Computing Classical ZABR with params:', JSON.stringify(req.query, null, 2));
  try {
    await ZabrAnalytics.getVolatilityData_classical(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for Mixture ZABR model endpoint
 */
module.exports.getVolatilityDataMixture = async function getVolatilityDataMixture(req, res, next) {
  console.log('Computing Mixture ZABR with params:', JSON.stringify(req.query, null, 2));
  try {
    await ZabrAnalytics.getVolatilityData_mixture(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for PDE SABR model endpoint
 */
module.exports.getVolatilityDataPde = async function getVolatilityDataPde(req, res, next) {
  console.log('Computing PDE SABR with params:', JSON.stringify(req.query, null, 2));
  try {
    await ZabrAnalytics.getVolatilityData_pde(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};

/**
 * Controller for ZABR calibration endpoint
 */
module.exports.getZabrCalibration = async function getZabrCalibration(req, res, next) {
  console.log('Computing ZABR calibration with params:', JSON.stringify(req.query, null, 2));
  try {
    await ZabrCalibration.getZabrCalibration(req, res);
  } catch (error) {
    return handleError(error, res);
  }
};