'use strict';

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { CONFIG, getPythonEnv } = require('./config');

exports.getVolatilityData_asv = async function(req, res) {
  try {
    // Extract parameters from request
    const params = {
      fwd: parseFloat(req.query.fwd || 1.0),
      time: parseFloat(req.query.time || 0.333),
      ctrl_p: parseFloat(req.query.ctrl_p || 0.2),
      ctrl_c: parseFloat(req.query.ctrl_c || 0.2),
      atm: parseFloat(req.query.atm || 0.1929),
      skew: parseFloat(req.query.skew || 0.02268),
      smile: parseFloat(req.query.smile || 0.003),
      put: parseFloat(req.query.put || 0.0384),
      call: parseFloat(req.query.call || 0.0001)
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

    console.log('Executing volatility_asv with:');
    console.log('XSigma Python Path:', CONFIG.PYTHON.EXECUTABLE);
    console.log('Script Path:', pythonScriptPath);
    console.log('Parameters:', params);

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