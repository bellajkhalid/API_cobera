'use strict';

const path = require('path');
const { spawn } = require('child_process');
const { CONFIG, validateParams, getPythonEnv } = require('./config');
const { LRUCache } = require('lru-cache'); // Updated import syntax for lru-cache v7+

/**
 * Custom error classes for better error handling and client responses
 */
class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
    this.status = 400;
  }
}

class PythonProcessError extends Error {
  constructor(message, code, stderr) {
    super(message);
    this.name = 'PythonProcessError';
    this.status = 500;
    this.code = code;
    this.stderr = stderr;
  }
}

class TimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = 'TimeoutError';
    this.status = 504; // Gateway Timeout
  }
}

/**
 * Cache configuration for storing computation results
 * Using LRU (Least Recently Used) cache strategy with a maximum of 100 entries
 * Each entry will expire after 15 minutes to ensure fresh data for long-running applications
 */
const resultCache = new LRUCache({
  max: 100,  // Store max 100 results
  ttl: 1000 * 60 * 15  // Cache for 15 minutes (using ttl instead of maxAge for newer versions)
});

/**
 * Handles the POST request for AnalyticalSigmaVolatilityCalibration
 * This endpoint performs volatility model calibration based on the provided parameters
 * and returns either volatility data or density function values depending on the computation type
 * 
 * @param {Object} req - Express request object containing the calibration parameters
 * @param {Object} res - Express response object
 * @returns {Promise<void>} Async function that sends the JSON response
 */
exports.volatility_densityPOST = async function(req, res) {
  try {
    console.log('⚡ Processing AnalyticalSigmaVolatilityCalibration request...');
    const startTime = Date.now();
    
    const params = req.body;
    
    // Validate parameters using the helper function
    try {
      validateParams(params);
    } catch (error) {
      throw new ValidationError(error.message);
    }

    // Generate cache key based on input parameters
    const cacheKey = JSON.stringify(params);
    
    // Check if result is in cache
    const cachedResult = resultCache.get(cacheKey);
    if (cachedResult) {
      console.log('💾 Cache hit! Returning cached result');
      // Add cache metadata to the response
      const responseWithCacheInfo = {
        ...cachedResult,
        meta: {
          ...cachedResult.meta,
          cached: true,
          timestamp: new Date().toISOString()
        }
      };
      
      return res.json(responseWithCacheInfo);
    }
    
    console.log('🔍 Cache miss. Computing result...');

    // Set up paths
    const pythonScriptPath = path.join(__dirname, 'Python', 'AnalyticalSigmaVolatilityCalibration.py');

    // Prepare command line arguments
    const args = [
      pythonScriptPath,
      ...CONFIG.REQUIRED_PARAMS.map(param => params[param].toString())
    ];

    // Log execution details
    console.log('📊 Computing Analytical Sigma Volatility with params:', params);
    console.log('[Configuration]', {
      pythonExecutable: CONFIG.PYTHON.EXECUTABLE,
      scriptPath: pythonScriptPath,
      arguments: args,
      workingDirectory: path.dirname(pythonScriptPath)
    });

    // Execute Python process
    const pythonProcess = spawn(CONFIG.PYTHON.EXECUTABLE, args, {
      env: getPythonEnv()
    });

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
      const str = data.toString();
      console.log('[Python stdout]:', str);
      dataString += str;
    });

    pythonProcess.stderr.on('data', (data) => {
      const str = data.toString();
      console.error('[Python stderr]:', str);
      errorString += str;
    });

    // Wait for process completion with timeout
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        reject(new TimeoutError(`Python process timed out after ${CONFIG.PYTHON.TIMEOUT_MS}ms`));
      }, CONFIG.PYTHON.TIMEOUT_MS);

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        console.log('[Python process] exited with code:', code);
        
        if (code !== 0) {
          reject(new PythonProcessError(
            `Python process exited with code ${code}`,
            code,
            errorString
          ));
        } else {
          resolve();
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        console.error('[Python process] failed to start:', error);
        reject(new PythonProcessError(`Failed to start Python process: ${error.message}`, -1, ''));
      });
    });

    try {
      // Find and parse JSON output
      const jsonMatch = dataString.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in Python output');
      }

      const result = JSON.parse(jsonMatch[0]);
      
      if (result.error) {
        throw new Error(result.error);
      }

      // Add performance metadata
      const processingTime = Date.now() - startTime;
      result.meta = {
        processingTime: `${processingTime}ms`,
        timestamp: new Date().toISOString(),
        computationType: params.computationType,
        cached: false
      };

      // Store result in cache
      resultCache.set(cacheKey, result);
      console.log(`✅ Calculation completed in ${processingTime}ms`);

      return res.json(result);
    } catch (e) {
      throw new Error('Failed to parse Python output: ' + e.toString());
    }
  } catch (error) {
    console.error('❌ [Error]', error);
    
    const statusCode = error.status || 500;
    const errorResponse = {
      status: 'error',
      error: error.message,
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
    
    res.status(statusCode).json(errorResponse);
  }
};