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
      ? 'C:/dev/build_ninja_avx2_python_sphinx/bin/xsigmapython.exe'
      : '/usr/local/bin/xsigmapython'),
    SITE_PACKAGES: process.env.PYTHONPATH || (process.platform === 'win32'
      ? 'C:/dev/build_ninja_avx2_python_sphinx/lib/python3.12/site-packages'
      : '/usr/local/lib/python3.12/site-packages'),
    DATA_ROOT: process.env.XSIGMA_DATA_ROOT || (process.platform === 'win32'
      ? 'C:/dev/build_ninja_avx2_python_sphinx/ExternalData/Testing'
      : '/usr/local/share/xsigma/data'),
    TIMEOUT_MS: parseInt(process.env.PYTHON_TIMEOUT_MS, 10) || 30000,
    // Ajout des chemins Python supplémentaires
    XSIGMA_MODULE_PATH: process.env.XSIGMA_MODULE_PATH || (process.platform === 'win32'
      ? 'C:/dev/build_ninja_avx2_python_sphinx/lib/python3.11/site-packages/xsigmamodules'
      : '/usr/local/lib/python3.11/site-packages/xsigmamodules'),
    PYTHON_SERVICE_PATH: process.env.PYTHON_SERVICE_PATH || path.join(__dirname, 'Python'),
    PYTHON_COMMON_PATH: process.env.PYTHON_COMMON_PATH || path.join(__dirname, 'Python', 'common')
  },
  VALID_COMPUTATION_TYPES: ['volatility_asv', 'density', 'volatility_svi'],
  REQUIRED_PARAMS: [
    'n', 'spot', 'expiry', 'r', 'q', 
    'beta', 'rho', 'volvol', 'computationType'
  ],
  NUMERIC_PARAMS: ['n', 'spot', 'expiry', 'r', 'q', 'beta', 'rho', 'volvol'],
  // New detailed parameter validation rules
  PARAM_RULES: {
    n: { type: 'integer', min: 1, max: 10000, description: 'Number of points for calculation' },
    spot: { type: 'number', min: 0.001, description: 'Spot price' },
    expiry: { type: 'number', min: 0.001, max: 100, description: 'Time to expiry in years' },
    r: { type: 'number', min: -0.10, max: 0.50, description: 'Risk-free interest rate' },
    q: { type: 'number', min: -0.10, max: 0.50, description: 'Dividend yield' },
    beta: { type: 'number', min: 0, max: 1, description: 'Beta parameter' },
    rho: { type: 'number', min: -1, max: 1, description: 'Correlation parameter' },
    volvol: { type: 'number', min: 0.001, description: 'Volatility of volatility' },
    computationType: { 
      type: 'string', 
      enum: ['volatility_asv', 'density', 'volatility_svi'],
      description: 'Type of computation to perform'
    }
  }
};

/**
 * Helper function to validate parameters with enhanced error messages
 * @param {Object} params - Request parameters to validate
 * @throws {Error} If validation fails
 */
function validateParams(params) {
  // Check required parameters and validate against rules
  for (const [param, rules] of Object.entries(CONFIG.PARAM_RULES)) {
    // Check if parameter exists
    if (!(param in params)) {
      throw new Error(`Missing required parameter: ${param} (${rules.description})`);
    }
    
    const value = params[param];
    
    // Type checking
    if (rules.type === 'number' && (typeof value !== 'number' || isNaN(value))) {
      throw new Error(`Parameter ${param} must be a number (${rules.description})`);
    } 
    else if (rules.type === 'integer' && (!Number.isInteger(Number(value)) || isNaN(Number(value)))) {
      throw new Error(`Parameter ${param} must be an integer (${rules.description})`);
    }
    else if (rules.type === 'string' && typeof value !== 'string') {
      throw new Error(`Parameter ${param} must be a string (${rules.description})`);
    }
    
    // Range checking for numeric types
    if (rules.min !== undefined && Number(value) < rules.min) {
      throw new Error(`Parameter ${param} must be at least ${rules.min} (${rules.description})`);
    }
    if (rules.max !== undefined && Number(value) > rules.max) {
      throw new Error(`Parameter ${param} must be at most ${rules.max} (${rules.description})`);
    }
    
    // Enum checking
    if (rules.enum && !rules.enum.includes(value)) {
      throw new Error(`Parameter ${param} must be one of: ${rules.enum.join(', ')} (${rules.description})`);
    }
  }
}

// Helper function to get Python process environment
function getPythonEnv() {
  // Construire le PYTHONPATH avec tous les chemins nécessaires
  const pythonPaths = [
    CONFIG.PYTHON.SITE_PACKAGES,
    CONFIG.PYTHON.PYTHON_SERVICE_PATH,
    CONFIG.PYTHON.PYTHON_COMMON_PATH
  ].filter(Boolean).join(process.platform === 'win32' ? ';' : ':');
  
  return {
    ...process.env,
    PYTHONPATH: pythonPaths,
    XSIGMA_DATA_ROOT: CONFIG.PYTHON.DATA_ROOT,
    PYTHONUNBUFFERED: '1'
  };
}

module.exports = {
  CONFIG,
  validateParams,
  getPythonEnv
};