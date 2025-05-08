'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { CONFIG, getPythonEnv } = require('./config');

// Parameter validation rules
const PARAM_RULES = {
  fwd: { min: 0.1, max: 10.0, default: 1.0 },
  time: { min: 0.1, max: 2.0, default: 0.333 },
  b: { min: 0.01, max: 1.0, default: 0.1 },
  m: { min: -5.0, max: 5.0, default: 0.01 },
  sigma: { min: 0.1, max: 1.0, default: 0.4 }
};

/**
 * Validates a numeric parameter against defined rules
 */
function validateParameter(name, value, rules) {
  const num = Number(value);
  if (isNaN(num)) {
    throw new Error(`Invalid ${name}: ${value} is not a number`);
  }
  if (num < rules.min || num > rules.max) {
    throw new Error(`${name} must be between ${rules.min} and ${rules.max}, got: ${num}`);
  }
  return num;
}

/**
 * Process and validate input parameters
 */
function processParameters(query) {
  const params = {};
  for (const [key, rules] of Object.entries(PARAM_RULES)) {
    const value = query[key] !== undefined ? query[key] : rules.default;
    params[key] = validateParameter(key, value, rules);
  }
  return params;
}

exports.getVolatilityDataSvi = async function(req, res) {
  try {
    // Extract parameters from request
    const params = processParameters(req.query);

    // Get absolute paths
    const projectRoot = path.resolve(__dirname, '..');
    const pythonScriptPath = path.join(projectRoot, 'service', 'Python', 'volatility_svi.py');
    
    // Verify Python script exists
    if (!fs.existsSync(pythonScriptPath)) {
      console.error('Python script not found at:', pythonScriptPath);
      throw new Error(`Python script not found at: ${pythonScriptPath}`);
    }

    console.log('Executing with:', {
      pythonPath: CONFIG.PYTHON.EXECUTABLE,
      scriptPath: pythonScriptPath,
      params: params
    });

    // Create Python process using centralized configuration
    const pythonProcess = spawn(
      CONFIG.PYTHON.EXECUTABLE, 
      [pythonScriptPath, JSON.stringify(params)], 
      {
        env: getPythonEnv(),
        cwd: path.dirname(pythonScriptPath),
        stdio: ['pipe', 'pipe', 'pipe']
      }
    );

    let dataString = '';
    let errorString = '';

    // Handle stdout data
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Python stdout:', output);
      dataString += output;
    });

    // Handle stderr data
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      console.error('Python stderr:', error);
      errorString += error;
    });

    // Wait for process completion
    await new Promise((resolve, reject) => {
      // Handle process completion
      pythonProcess.on('close', (code) => {
        console.log('Python process exited with code:', code);
        if (code !== 0) {
          reject(new Error(`Python process failed with code ${code}\nError: ${errorString}`));
          return;
        }

        try {
          // Find the last valid JSON in the output
          const jsonMatch = dataString.match(/\{[\s\S]*\}/g);
          if (!jsonMatch) {
            throw new Error('No valid JSON found in output');
          }
          const lastJson = jsonMatch[jsonMatch.length - 1];
          const result = JSON.parse(lastJson);
          
          res.json({
            status: 'success',
            data: result
          });
          resolve();
        } catch (e) {
          console.error('Failed to parse Python output:', e);
          console.error('Raw output:', dataString);
          reject(new Error(`Invalid Python output: ${e.toString()}\nRaw output: ${dataString}`));
        }
      });

      // Handle process errors
      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        reject(new Error(`Failed to start Python process: ${error.message}`));
      });

      // Set timeout using CONFIG
      setTimeout(() => {
        pythonProcess.kill();
        reject(new Error(`Python process timed out after ${CONFIG.PYTHON.TIMEOUT_MS / 1000} seconds`));
      }, CONFIG.PYTHON.TIMEOUT_MS);
    });

  } catch (error) {
    console.error('Service error:', error);
    const status = error.status || 500;
    res.status(status).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};