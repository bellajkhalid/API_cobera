// config.js
'use strict';

const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from .env file
dotenv.config();

// Configuration constants with environment variable fallbacks
const CONFIG = {
  PYTHON: {
    EXECUTABLE: process.env.PYTHON_EXECUTABLE || (process.platform === 'win32' 
      ? 'C:/dev/build_ninja_avx2_python/bin/xsigmapython.exe'
      : '/usr/local/bin/xsigmapython'),
    SITE_PACKAGES: process.env.PYTHONPATH || (process.platform === 'win32'
      ? 'C:/dev/build_ninja_avx2_python/lib/python3.12/site-packages'
      : '/usr/local/lib/python3.12/site-packages'),
    DATA_ROOT: process.env.XSIGMA_DATA_ROOT || (process.platform === 'win32'
      ? 'C:/dev/build_ninja_avx2_python/ExternalData/Testing'
      : '/usr/local/share/xsigma/data'),
    TIMEOUT_MS: parseInt(process.env.PYTHON_TIMEOUT_MS, 10) || 30000,
  },
  VALID_COMPUTATION_TYPES: ['volatility_asv', 'density', 'volatility_svi'],
  REQUIRED_PARAMS: [
    'n', 'spot', 'expiry', 'r', 'q', 
    'beta', 'rho', 'volvol', 'computationType'
  ],
  NUMERIC_PARAMS: ['n', 'spot', 'expiry', 'r', 'q', 'beta', 'rho', 'volvol']
};

// Helper function to validate parameters
function validateParams(params) {
  // Check required parameters
  for (const param of CONFIG.REQUIRED_PARAMS) {
    if (!(param in params)) {
      throw new Error(`Missing required parameter: ${param}`);
    }
  }

  // Validate numeric parameters
  for (const param of CONFIG.NUMERIC_PARAMS) {
    if (isNaN(params[param])) {
      throw new Error(`Invalid numeric value for parameter: ${param}`);
    }
  }

  // Validate computation type
  if (!CONFIG.VALID_COMPUTATION_TYPES.includes(params.computationType)) {
    throw new Error(
      `Invalid computation type. Must be one of: ${CONFIG.VALID_COMPUTATION_TYPES.join(', ')}`
    );
  }
}

// Helper function to get Python process environment
function getPythonEnv() {
  return {
    ...process.env,
    PYTHONPATH: CONFIG.PYTHON.SITE_PACKAGES,
    XSIGMA_DATA_ROOT: CONFIG.PYTHON.DATA_ROOT,
    PYTHONUNBUFFERED: '1'
  };
}

module.exports = {
  CONFIG,
  validateParams,
  getPythonEnv
};