'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const XSIGMA_PYTHON = 'C:/dev/build_ninja_avx2_python/bin/xsigmapython.exe';
const XSIGMA_SITE_PACKAGES = 'C:/dev/build_ninja_avx2_python/lib/python3.12/site-packages';

exports.getVolatilityData_classical = async function(req, res) {
  try {
    const {
      expiry = 10.0,
      forward = 0.0325,
      alpha = 0.0873,
      beta = 0.7,
      nu = 0.47,
      rho = -0.48,
      shift = 0.0,
      gamma = 1.0,
      use_vol_adjustement = true
    } = req.query;

    const params = {
      model_type: 'classical',
      expiry: parseFloat(expiry),
      forward: parseFloat(forward),
      alpha: parseFloat(alpha),
      beta: parseFloat(beta),
      nu: parseFloat(nu),
      rho: parseFloat(rho),
      shift: parseFloat(shift),
      gamma: parseFloat(gamma),
      use_vol_adjustement: use_vol_adjustement === 'true'
    };

    return await executePythonScript(params, res);
  } catch (error) {
    handleError(error, res);
  }
};

exports.getVolatilityData_mixture = async function(req, res) {
  try {
    const {
      expiry = 30,
      forward = -0.0007,
      alpha = 0.0132,
      beta1 = 0.2,
      beta2 = 1.25,
      d = 0.2,
      nu = 0.1978,
      rho = -0.444,
      gamma = 1.0,
      use_vol_adjustement = true,
      high_strike = 0.1,
      vol_low = 0.0001,
      low_strike = 0.02,
      forward_cut_off = 0.02,
      smothing_factor = 0.001
    } = req.query;

    const params = {
      model_type: 'mixture',
      expiry: parseFloat(expiry),
      forward: parseFloat(forward),
      alpha: parseFloat(alpha),
      beta1: parseFloat(beta1),
      beta2: parseFloat(beta2),
      d: parseFloat(d),
      nu: parseFloat(nu),
      rho: parseFloat(rho),
      gamma: parseFloat(gamma),
      use_vol_adjustement: use_vol_adjustement === 'true',
      high_strike: parseFloat(high_strike),
      vol_low: parseFloat(vol_low),
      low_strike: parseFloat(low_strike),
      forward_cut_off: parseFloat(forward_cut_off),
      smothing_factor: parseFloat(smothing_factor)
    };

    return await executePythonScript(params, res);
  } catch (error) {
    handleError(error, res);
  }
};

exports.getVolatilityData_pde = async function(req, res) {
  try {
    const {
      expiry = 30.0,
      forward = 0.02,
      alpha = 0.035,
      beta = 0.25,
      nu = 1.0,
      rho = -0.1,
      shift = 0.0,
      N = 100,
      timesteps = 5,
      nd = 5
    } = req.query;

    const params = {
      model_type: 'pde',
      expiry: parseFloat(expiry),
      forward: parseFloat(forward),
      alpha: parseFloat(alpha),
      beta: parseFloat(beta),
      nu: parseFloat(nu),
      rho: parseFloat(rho),
      shift: parseFloat(shift),
      N: parseInt(N),
      timesteps: parseInt(timesteps),
      nd: parseInt(nd)
    };

    return await executePythonScript(params, res);
  } catch (error) {
    handleError(error, res);
  }
};

async function executePythonScript(params, res) {
  // Get absolute paths
  const projectRoot = path.resolve(__dirname, '..');
  const pythonScriptPath = path.join(projectRoot, 'service', 'Python', 'zabr_analytics.py');
  
  // Verify Python script exists
  if (!fs.existsSync(pythonScriptPath)) {
    throw createError(`Python script not found at: ${pythonScriptPath}`, 500);
  }

  // Set up environment variables
  const env = {
    ...process.env,
    PYTHONPATH: [
      XSIGMA_SITE_PACKAGES,
      path.dirname(pythonScriptPath),
      process.env.PYTHONPATH || ''
    ].join(path.delimiter),
    PYTHONUNBUFFERED: '1',
    XSIGMA_DATA_ROOT: 'C:/dev/build_ninja_avx2_python/ExternalData/Testing'
  };

  console.log('Executing with:');
  console.log('XSigma Python Path:', XSIGMA_PYTHON);
  console.log('Script Path:', pythonScriptPath);
  console.log('PYTHONPATH:', env.PYTHONPATH);
  console.log('Working Directory:', path.dirname(pythonScriptPath));
  console.log('Parameters:', params);

  // Create Python process
  const pythonProcess = spawn(
    XSIGMA_PYTHON, 
    [pythonScriptPath, JSON.stringify(params)], 
    {
      env,
      cwd: path.dirname(pythonScriptPath),
      stdio: ['pipe', 'pipe', 'pipe']
    }
  );

  let dataString = '';
  let errorString = '';

  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    console.log('Python stdout:', output);
    dataString += output;
  });

  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString();
    console.error('Python stderr:', error);
    errorString += error;
  });

  await new Promise((resolve, reject) => {
    pythonProcess.on('close', (code) => {
      console.log('Python process exited with code:', code);
      if (code !== 0) {
        reject(createError(
          `Python process exited with code ${code}\nError: ${errorString}`,
          500
        ));
      } else {
        resolve();
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      reject(createError(`Failed to start XSigma Python process: ${error.message}`, 500));
    });

    // Add timeout
    setTimeout(() => {
      pythonProcess.kill();
      reject(createError('Python process timed out after 30 seconds', 500));
    }, 30000);
  });

  try {
    // Find the last valid JSON in the output
    const jsonMatch = dataString.match(/\{[\s\S]*\}/g);
    if (!jsonMatch) {
      throw new Error('No valid JSON found in output');
    }
    const lastJson = jsonMatch[jsonMatch.length - 1];
    const result = JSON.parse(lastJson);
    return res.json({
      status: 'success',
      data: result
    });
  } catch (e) {
    console.error('Failed to parse Python output:', e);
    console.error('Raw output:', dataString);
    throw createError(
      `Invalid Python output: ${e.toString()}\nRaw output: ${dataString}`,
      500
    );
  }
}

function createError(message, status = 500) {
  const error = new Error(message);
  error.status = status;
  return error;
}

function handleError(error, res) {
  if (!error.status) {
    error.status = 500;
  }
  res.status(error.status).json({
    status: 'error',
    error: error.message
  });
}