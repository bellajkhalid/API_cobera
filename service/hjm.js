// hjm.js
'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { CONFIG, getPythonEnv } = require('./config');

exports.getHjmCalibration = async function(req, res) {
  try {
    // Extract parameters from request
    const test = parseInt(req.query.test || '1');

    // Validate parameter
    if (![1, 2, 3].includes(test)) {
      const error = new Error('test parameter must be 1, 2, or 3');
      error.status = 400;
      throw error;
    }

    // Get absolute paths
    const projectRoot = path.resolve(__dirname, '..');
    const pythonScriptPath = path.join(projectRoot, 'service', 'Python', 'HJM.py');
    
    // Verify Python script exists
    if (!fs.existsSync(pythonScriptPath)) {
      console.error('Python script not found at:', pythonScriptPath);
      const error = new Error(`Python script not found at: ${pythonScriptPath}`);
      error.status = 500;
      throw error;
    }

    console.log('Executing with:');
    console.log('XSigma Python Path:', CONFIG.PYTHON.EXECUTABLE);
    console.log('Script Path:', pythonScriptPath);
    console.log('Working Directory:', path.dirname(pythonScriptPath));
    console.log('Test Parameter:', test);

    // Increase timeout for test 2
    const timeout = req.query.test === '2' ? 120000 : CONFIG.PYTHON.TIMEOUT_MS;

    // Create Python process using centralized configuration
    const pythonProcess = spawn(CONFIG.PYTHON.EXECUTABLE, [pythonScriptPath, test.toString()], {
      env: getPythonEnv(),
      cwd: path.dirname(pythonScriptPath),
      stdio: ['pipe', 'pipe', 'pipe']
    });

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

      setTimeout(() => {
        pythonProcess.kill();
        reject(new Error(`Python process timed out after ${timeout/1000} seconds`));
      }, timeout);
    });

    try {
      // Find the last valid JSON in the output
      const jsonMatch = dataString.match(/\{[\s\S]*\}/g);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in output');
      }
      const lastJson = jsonMatch[jsonMatch.length - 1];
      const result = JSON.parse(lastJson);
      return res.json(result);
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