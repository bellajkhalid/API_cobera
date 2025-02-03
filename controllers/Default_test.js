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