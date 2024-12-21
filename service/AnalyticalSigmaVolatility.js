// AnalyticalSigmaVolatilityCalibration.js
'use strict';

const path = require('path');
const { spawn } = require('child_process');


exports.getAnalyticalSigmaVolatility = async function(req, res) {
  try {
    // Extract parameters from request with defaults
    const params = {
      n: parseInt(req.query.n || '200'),
      fwd: parseFloat(req.query.fwd || '1.0'),
      time: parseFloat(req.query.time || '0.333'),
      ctrl_p: parseFloat(req.query.ctrl_p || '0.2'),
      ctrl_c: parseFloat(req.query.ctrl_c || '0.2'),
      atm: parseFloat(req.query.atm || '0.1929'),
      skew: parseFloat(req.query.skew || '0.02268'),
      smile: parseFloat(req.query.smile || '0.00317'),
      put: parseFloat(req.query.put || '-0.00213'),
      call: parseFloat(req.query.call || '-0.00006'),
      Test: parseInt(req.query.Test || '1')
    };

    // Validate all parameters are numbers
    for (const [key, value] of Object.entries(params)) {
      if (isNaN(value)) {
        throw new Error(`Invalid numeric value for parameter: ${key}`);
      }
    }

    // Create Python process
    const pythonScriptPath = path.join(__dirname, './Python/AnalyticalSigmaVolatility.py');
    const pythonProcess = spawn('python', [
      pythonScriptPath,
      params.n.toString(),
      params.fwd.toString(),
      params.time.toString(),
      params.ctrl_p.toString(),
      params.ctrl_c.toString(),
      params.atm.toString(),
      params.skew.toString(),
      params.smile.toString(),
      params.put.toString(),
      params.call.toString(),
      params.Test.toString()
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
          reject(new Error(`Python process exited with code ${code}\nError: ${errorString}`));
        } else {
          resolve();
        }
      });

      pythonProcess.on('error', (error) => {
        reject(new Error(`Failed to start Python process: ${error.message}`));
      });
    });

    try {
      const result = JSON.parse(dataString);
      res.json(result);
    } catch (e) {
      res.status(500).json({
        error: 'Invalid Python output',
        message: e.toString(),
        output: dataString
      });
    }
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({
      error: 'Calculation error',
      message: error.toString()
    });
  }
};