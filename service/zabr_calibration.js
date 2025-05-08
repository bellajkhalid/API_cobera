'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { CONFIG, getPythonEnv } = require('./config');

exports.getZabrCalibration = async function(req, res) {
  try {
    // Extract parameters from request with defaults
    const {
      N = 401,
      forward = 0.02,
      expiry = 30,
      alpha = 0.00955,
      beta = 0.956,
      vol_of_vol = 0.373,
      rho = -0.749,
      shift = 0.0,
      gamma = 1.0,
      calibration_type = 'classical',
      dt = 5.0,
      nd = 3.5
    } = req.query;

    // Parse params and create object
    const params = {
      N: parseInt(N),
      forward: parseFloat(forward),
      expiry: parseFloat(expiry),
      alpha: parseFloat(alpha),
      beta: parseFloat(beta),
      vol_of_vol: parseFloat(vol_of_vol),
      rho: parseFloat(rho),
      shift: parseFloat(shift),
      gamma: parseFloat(gamma),
      calibration_type: calibration_type,
      dt: parseFloat(dt),
      nd: parseFloat(nd)
    };

    // Validate numeric parameters
    for (const [key, value] of Object.entries(params)) {
      if (key !== 'calibration_type' && isNaN(value)) {
        return res.status(400).json({
          status: 'error',
          error: `Invalid numeric value for parameter: ${key}`
        });
      }
    }

    // Additional parameter validation
    if (params.N <= 0) {
      return res.status(400).json({
        status: 'error',
        error: 'N must be positive'
      });
    }

    if (params.beta < 0 || params.beta > 1) {
      return res.status(400).json({
        status: 'error',
        error: 'beta must be between 0 and 1'
      });
    }

    if (params.rho < -1 || params.rho > 1) {
      return res.status(400).json({
        status: 'error',
        error: 'rho must be between -1 and 1'
      });
    }

    // Validate calibration type
    const validCalibrationTypes = ['classical', 'pde', 'mixture'];
    if (!validCalibrationTypes.includes(params.calibration_type)) {
      return res.status(400).json({
        status: 'error',
        error: `Invalid calibration type. Must be one of: ${validCalibrationTypes.join(', ')}`
      });
    }

    // Get absolute paths
    const projectRoot = path.resolve(__dirname, '..');
    const pythonScriptPath = path.join(projectRoot, 'service', 'Python', 'zabr_calibration.py');
    
    // Verify Python script exists
    if (!fs.existsSync(pythonScriptPath)) {
      console.error('Python script not found at:', pythonScriptPath);
      throw new Error(`Python script not found at: ${pythonScriptPath}`);
    }

    console.log('Executing zabr_calibration with parameters:', params);
    console.log('Using Python executable:', CONFIG.PYTHON.EXECUTABLE);

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

    // Wait for process completion
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
      throw new Error(`Failed to parse Python output: ${e.toString()}\nOutput: ${dataString}`);
    }
  } catch (error) {
    console.error('[Error]', error);
    res.status(500).json({
      status: 'error',
      error: error.message
    });
  }
};