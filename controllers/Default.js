'use strict';

const utils = require('../utils/writer.js');
const AnalyticalSigmaVolatilityCalibration = require('../service/AnalyticalSigmaVolatilityCalibration.js');
const AnalyticalSigmaVolatility = require('../service/AnalyticalSigmaVolatility.js');
const HartmanWatsonDistribution = require('../service/HW_distribution.js');
const HjmCalibration = require('../service/hjm.js');
const MHJMRates = require('../service/LognormalFXWithMHJMRate.js');
const ZabrCalibration = require('../service/zabr_calibration.js');
const VolatilitySvi = require('../service/volatility_svi.js');
const VolatilityAsv = require('../service/volatility_asv.js');
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

/**
 * Controller for Analytical Sigma Volatility Calibration POST endpoint
 */
module.exports.volatility_densityPOST = async function volatility_densityPOST(req, res, next) {
  console.log('Computing analytical sigma volatility with params:', JSON.stringify(req.body, null, 2));
  try {
    await AnalyticalSigmaVolatilityCalibration.volatility_densityPOST(req, res);
  } catch (error) {
    return handleError(error, res);
  }
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

// Maintain backward compatibility with old endpoint names
module.exports.updateVolatilityData_svi = module.exports.getVolatilitySvi;
module.exports.updateVolatilityData_asv = module.exports.getVolatilityAsv;
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
/**
 * Controller for test endpoint
 */
module.exports.testGET = async function testGET(req, res, next) {
  try {
    const response = await Default.testGET();
    utils.writeJson(res, response);
  } catch (error) {
    return handleError(error, res);
  }
};