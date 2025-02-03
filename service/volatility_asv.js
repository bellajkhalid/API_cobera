'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const XSIGMA_PYTHON = 'C:/dev/build_ninja_avx2_python/bin/xsigmapython.exe';
const XSIGMA_SITE_PACKAGES = 'C:/dev/build_ninja_avx2_python/lib/python3.12/site-packages';

exports.getVolatilityData_asv = async function(req, res) {
  try {
    // Extract parameters from request
    const {
      fwd = 1.0,
      time = 0.333,
      ctrl_p = 0.2,
      ctrl_c = 0.2,
      atm = 0.1929,
      skew = 0.02268,
      smile = 0.003,
      put = 0.0384,
      call = 0.0001
    } = req.query;

    // Validate parameters
    const params = {
      fwd: parseFloat(fwd),
      time: parseFloat(time),
      ctrl_p: parseFloat(ctrl_p),
      ctrl_c: parseFloat(ctrl_c),
      atm: parseFloat(atm),
      skew: parseFloat(skew),
      smile: parseFloat(smile),
      put: parseFloat(put),
      call: parseFloat(call)
    };

    // Get absolute paths
    const projectRoot = path.resolve(__dirname, '..');
    const pythonScriptPath = path.join(projectRoot, 'service', 'Python', 'volatility.py');
    
    // Verify Python script exists
    if (!fs.existsSync(pythonScriptPath)) {
      console.error('Python script not found at:', pythonScriptPath);
      const error = new Error(`Python script not found at: ${pythonScriptPath}`);
      error.status = 500;
      throw error;
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
          const error = new Error(
            `Python process exited with code ${code}\n` +
            `Error: ${errorString}`
          );
          error.status = 500;
          reject(error);
        } else {
          resolve();
        }
      });

      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        error.status = 500;
        reject(new Error(`Failed to start XSigma Python process: ${error.message}`));
      });

      // Add timeout
      setTimeout(() => {
        pythonProcess.kill();
        reject(new Error('Python process timed out after 30 seconds'));
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
      const error = new Error(`Invalid Python output: ${e.toString()}\nRaw output: ${dataString}`);
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