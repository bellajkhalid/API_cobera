'use strict';

const { validateParams } = require('../service/config');

/**
 * Middleware to validate request body against schema for the AnalyticalSigmaVolatilityCalibration endpoint
 * This middleware ensures all required parameters are present and valid before the request reaches the controller
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
function validateVolatilityCalibrationRequest(req, res, next) {
  try {
    // Perform validation using the enhanced validation function
    validateParams(req.body);
    
    // If validation passes, proceed to the next middleware or controller
    next();
  } catch (error) {
    // If validation fails, return a 400 Bad Request response with details
    res.status(400).json({
      status: 'error',
      error: error.message,
      errorType: 'ValidationError',
      timestamp: new Date().toISOString()
    });
  }
}

/**
 * Generic request body validation middleware that can be adapted for different endpoints
 * 
 * @param {Function} validationFn - The validation function to use
 * @returns {Function} Express middleware function
 */
function validateRequestBody(validationFn) {
  return (req, res, next) => {
    try {
      validationFn(req.body);
      next();
    } catch (error) {
      res.status(400).json({
        status: 'error',
        error: error.message,
        errorType: 'ValidationError',
        timestamp: new Date().toISOString()
      });
    }
  };
}

module.exports = {
  validateVolatilityCalibrationRequest,
  validateRequestBody
};