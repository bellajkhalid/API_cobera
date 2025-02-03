'use strict';

const path = require('path');
const { spawn } = require('child_process');

// Configuration constants
const PYTHON_CONFIG = {
  EXECUTABLE: process.platform === 'win32' 
    ? 'C:/dev/build_ninja_avx2_python/bin/xsigmapython.exe'
    : '/usr/local/bin/xsigmapython',
  SITE_PACKAGES: process.platform === 'win32'
    ? 'C:/dev/build_ninja_avx2_python/lib/python3.12/site-packages'
    : '/usr/local/lib/python3.12/site-packages',
  DATA_ROOT: process.platform === 'win32'
    ? 'C:/dev/build_ninja_avx2_python/ExternalData/Testing'
    : '/usr/local/share/xsigma/data',
  TIMEOUT_MS: 30000
};

exports.getZabrCalibration = async function(req, res) {
  try {
    // Extract parameters from request with defaults
    const params = {
      N: parseInt(req.query.N || '401'),
      forward: parseFloat(req.query.forward || '0.02'),
      expiry: parseFloat(req.query.expiry || '30'),
      alpha: parseFloat(req.query.alpha || '0.00955'),
      beta: parseFloat(req.query.beta || '0.956'),
      vol_of_vol: parseFloat(req.query.vol_of_vol || '0.373'),
      rho: parseFloat(req.query.rho || '-0.749'),
      shift: parseFloat(req.query.shift || '0.0'),
      gamma: parseFloat(req.query.gamma || '1.0'),
      dt: parseFloat(req.query.dt || '5.0'),
      nd: parseFloat(req.query.nd || '3.5'),
      calibration_type: req.query.calibration_type || 'classical'
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

    // Set up paths
    const pythonScriptPath = path.join(__dirname, 'Python', 'zabr_calibration.py');

// Prepare command line arguments
const args = [
  pythonScriptPath,
  params.forward.toString(),
  params.expiry.toString(),
  params.alpha.toString(),
  params.beta.toString(),
  params.vol_of_vol.toString(),
  params.rho.toString(),
  params.shift.toString(),
  params.gamma.toString(),
  params.calibration_type
];

// Add PDE specific parameters if needed
if (params.calibration_type === 'pde') {
  args.push(params.dt.toString());
  args.push(params.nd.toString());
}

// Log execution details
console.log('Computing ZABR calibration with params:', params);
console.log('[Configuration]', {
  pythonExecutable: PYTHON_CONFIG.EXECUTABLE,
  scriptPath: pythonScriptPath,
  arguments: args,
  workingDirectory: path.dirname(pythonScriptPath)
});

// Execute Python process
const pythonProcess = spawn(PYTHON_CONFIG.EXECUTABLE, args, {
  env: {
    ...process.env,
    PYTHONPATH: PYTHON_CONFIG.SITE_PACKAGES,
    XSIGMA_DATA_ROOT: PYTHON_CONFIG.DATA_ROOT,
    PYTHONUNBUFFERED: '1'
  }
});

// Add more detailed logging for Python process errors
pythonProcess.stderr.on('data', (data) => {
  const str = data.toString();
  console.error('[Python stderr]:', str);
  errorString += str;
  // Log the error in a structured format
  console.error(JSON.stringify({
    timestamp: new Date().toISOString(),
    error: str,
    params: params
  }));
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

    // Wait for process completion
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        reject(new Error(`Python process timed out after ${PYTHON_CONFIG.TIMEOUT_MS}ms`));
      }, PYTHON_CONFIG.TIMEOUT_MS);

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