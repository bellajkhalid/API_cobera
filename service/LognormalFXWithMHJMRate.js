'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { CONFIG, getPythonEnv } = require('./config');

/**
 * Handle requests for the LognormalFXWithMHJMRates service
 */
exports.LognormalFXWithMHJMRates = async function(req, res) {
  try {
    console.log('Computing Lognormal FX with MHJM Rates with params:', req.query);

    // Extract parameters from request
    const num_paths = req.query.num_paths || '524288';
    const volatility = req.query.volatility || '0.15';

    // Get absolute paths
    const projectRoot = path.resolve(__dirname, '..');
    const pythonScriptPath = path.join(projectRoot, 'service', 'Python', 'LognormalFXWithMHJMRates.py');

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
    console.log('Parameters:', { num_paths, volatility });

    // Prepare command line arguments
    const args = [pythonScriptPath];
    if (num_paths) {
      args.push('--num-paths', num_paths);
    }
    if (volatility) {
      args.push('--volatility', volatility);
    }

    // Create Python process using centralized configuration
    const pythonProcess = spawn(CONFIG.PYTHON.EXECUTABLE, args, {
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

    // Use a longer timeout for this computation
    const timeout = 1200000; // 20 minutes

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
    console.error('[Error]', error);
    const statusCode = error.status || 500;
    res.status(statusCode).json({
      status: 'error',
      data: null,
      error: error.message
    });
  }
};