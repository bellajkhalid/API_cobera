'use strict';

const path = require('path');
const { spawn } = require('child_process');

// Configuration for Python environment
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

exports.getHartmanWatsonDistribution = async function(req, res) {
  try {
    // Extract parameters from request with defaults
    const params = {
      n: parseInt(req.query.n || '64'),
      t: parseFloat(req.query.t || '0.5'),
      size_roots: parseInt(req.query.size_roots || '32'),
      x_0: parseFloat(req.query.x_0 || '-5'),
      x_n: parseFloat(req.query.x_n || '3.1')
    };

    console.log('Computing Hartman-Watson distribution with params:', params);

    // Validate all parameters are numbers
    for (const [key, value] of Object.entries(params)) {
      if (isNaN(value)) {
        const error = new Error(`Invalid numeric value for parameter: ${key}`);
        error.status = 400;
        throw error;
      }
    }

    // Additional validation
    if (params.n <= 0) {
      const error = new Error('n must be positive');
      error.status = 400;
      throw error;
    }
    if (params.t <= 0) {
      const error = new Error('t must be positive');
      error.status = 400;
      throw error;
    }
    if (params.size_roots <= 0) {
      const error = new Error('size_roots must be positive');
      error.status = 400;
      throw error;
    }
    if (params.x_0 >= params.x_n) {
      const error = new Error('x_0 must be less than x_n');
      error.status = 400;
      throw error;
    }

    // Set up paths
    const pythonScriptPath = path.join(__dirname, './Python/HW_distribution.py');
    
    // Prepare the arguments array
    const args = [
      pythonScriptPath,
      params.n.toString(),
      params.t.toString(),
      params.size_roots.toString(),
      params.x_0.toString(),
      params.x_n.toString()
    ];

    // Log execution details
    console.log('[Configuration]', {
      pythonExecutable: PYTHON_CONFIG.EXECUTABLE,
      scriptPath: pythonScriptPath,
      arguments: args,
      workingDirectory: path.dirname(pythonScriptPath)
    });

    // Create Python process
    const pythonProcess = spawn(PYTHON_CONFIG.EXECUTABLE, args, {
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
      const result = JSON.parse(dataString);
      if (result.status === 'error') {
        const error = new Error(result.error);
        error.status = 500;
        throw error;
      }
      return res.json(result);
    } catch (e) {
      const error = new Error('Invalid Python output: ' + e.toString());
      error.status = 500;
      throw error;
    }
  } catch (error) {
    if (!error.status) {
      error.status = 500;
    }
    console.error('[Error]', error);
    res.status(error.status).json({
      status: 'error',
      data: null,
      error: error.message
    });
  }
};