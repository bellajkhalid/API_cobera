'use strict';

const path = require('path');
const { spawn } = require('child_process');
const { CONFIG, validateParams, getPythonEnv } = require('./config');

/**
 * Handles the POST request for AnalyticalSigmaVolatilityCalibration
 */
exports.volatility_densityPOST = async function(req, res) {
  try {
    const params = req.body;
    
    // Validate parameters using the helper function
    try {
      validateParams(params);
    } catch (error) {
      return res.status(400).json({
        status: 'error',
        error: error.message
      });
    }

    // Set up paths
    const pythonScriptPath = path.join(__dirname, 'Python', 'AnalyticalSigmaVolatilityCalibration.py');

    // Prepare command line arguments
    const args = [
      pythonScriptPath,
      ...CONFIG.REQUIRED_PARAMS.map(param => params[param].toString())
    ];

    // Log execution details
    console.log('Computing Analytical Sigma Volatility with params:', params);
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
        reject(new Error(`Python process timed out after ${CONFIG.PYTHON.TIMEOUT_MS}ms`));
      }, CONFIG.PYTHON.TIMEOUT_MS);

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        console.log('[Python process] exited with code:', code);
        
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}\nError: ${errorString}`));
        } else {
          resolve();
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        console.error('[Python process] failed to start:', error);
        reject(new Error(`Failed to start Python process: ${error.message}`));
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

      return res.json(result);
    } catch (e) {
      throw new Error('Failed to parse Python output: ' + e.toString());
    }
  } catch (error) {
    console.error('[Error]', error);
    res.status(500).json({
      status: 'error',
      error: error.message
    });
  }
};