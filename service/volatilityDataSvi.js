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

exports.getVolatilityDataSvi = async function(req, res) {
  try {
    // Extract parameters from request with defaults
    const params = {
      fwd: parseFloat(req.query.fwd || '1.0'),
      time: parseFloat(req.query.time || '0.333'),
      b: parseFloat(req.query.b || '0.1'),
      m: parseFloat(req.query.m || '0.01'),
      sigma: parseFloat(req.query.sigma || '0.4')
    };

    // Validate numeric parameters
    for (const [key, value] of Object.entries(params)) {
      if (isNaN(value)) {
        return res.status(400).json({
          status: 'error',
          error: `Invalid numeric value for parameter: ${key}`
        });
      }
    }

    // Set up paths
    const pythonScriptPath = path.join(__dirname, 'Python', 'volatility_svi.py');

    // Prepare process
    const pythonProcess = spawn(PYTHON_CONFIG.EXECUTABLE, [
      pythonScriptPath,
      JSON.stringify(params)
    ], {
      env: {
        ...process.env,
        PYTHONPATH: PYTHON_CONFIG.SITE_PACKAGES,
        XSIGMA_DATA_ROOT: PYTHON_CONFIG.DATA_ROOT,
        PYTHONUNBUFFERED: '1'
      }
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