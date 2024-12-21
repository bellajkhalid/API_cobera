'use strict';

const path = require('path');
const { spawn } = require('child_process');

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

    // Create Python process
    const pythonScriptPath = path.join(__dirname, './Python/HW_distribution.py');
    const pythonProcess = spawn('python', [
      pythonScriptPath,
      params.n.toString(),
      params.t.toString(),
      params.size_roots.toString(),
      params.x_0.toString(),
      params.x_n.toString()
    ]);

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorString += data.toString();
    });

    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          const error = new Error(`Python process exited with code ${code}\nError: ${errorString}`);
          error.status = 500;
          reject(error);
        } else {
          resolve();
        }
      });

      pythonProcess.on('error', (error) => {
        error.status = 500;
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
    throw error;
  }
};