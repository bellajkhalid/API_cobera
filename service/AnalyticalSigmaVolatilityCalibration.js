// AnalyticalSigmaVolatilityCalibration.js
'use strict';

const path = require('path');
const { spawn } = require('child_process');

exports.compute_volatility_density_POST = async function(body) {
  try {
    // Parameter validation
    const requiredParams = ['n', 'spot', 'expiry', 'r', 'q', 'beta', 'rho', 'volvol'];
    for (const param of requiredParams) {
      if (body[param] === undefined) {
        throw new Error(`Missing required parameter: ${param}`);
      }
    }

    // Parameter parsing with validation
    const params = {
      n: parseInt(body.n),
      spot: parseFloat(body.spot),
      expiry: parseFloat(body.expiry),
      r: parseFloat(body.r),
      q: parseFloat(body.q),
      beta: parseFloat(body.beta),
      rho: parseFloat(body.rho),
      volvol: parseFloat(body.volvol),
      computationType: body.computationType || 'volatility'
    };

    // Validate parsed numbers
    for (const [key, value] of Object.entries(params)) {
      if (key !== 'computationType' && isNaN(value)) {
        throw new Error(`Invalid numeric value for parameter: ${key}`);
      }
    }

    // Execute Python script with individual arguments instead of JSON string
    const pythonScriptPath = path.join(__dirname, './Python/AnalyticalSigmaVolatilityCalibration.py');
    
    return new Promise((resolve, reject) => {
      let dataString = '';
      let errorString = '';

      const pythonProcess = spawn('python', [
        pythonScriptPath,
        params.n.toString(),
        params.spot.toString(),
        params.expiry.toString(),
        params.r.toString(),
        params.q.toString(),
        params.beta.toString(),
        params.rho.toString(),
        params.volvol.toString(),
        params.computationType
      ]);

      pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}\nError: ${errorString}`));
          return;
        }

        try {
          const result = JSON.parse(dataString);
          resolve(result);
        } catch (error) {
          reject(new Error(`Failed to parse Python output: ${error.message}\nOutput: ${dataString}`));
        }
      });

      pythonProcess.on('error', (error) => {
        reject(new Error(`Failed to start Python process: ${error.message}`));
      });
    });
  } catch (error) {
    throw error;
  }
};
// Function test
exports.testGET = function() {
  return new Promise(function(resolve, reject) {
    const testData = [
      { key: 1.0E-4, value: 9.999999983333334E-5 },
      { key: 0.0012, value: 0.0011999997120000208 },
      { key: 0.0023, value: 0.002299997972167203 },
      { key: 0.0034, value: 0.0033999934493371196 },
      { key: 0.0045, value: 0.004499984812515378 },
      { key: 0.0056, value: 0.005599970730712562 },
      { key: 0.0067, value: 0.006699949872945844 },
      { key: 0.0078, value: 0.007799920908240598 },
      { key: 0.0089, value: 0.008899882505632005 },
      { key: 0.01, value: 0.009999833334166664 }
    ];
    resolve(testData);
  });
};


exports.getVolatilityData_asv = async (req, res) => {
  try {
    // Récupérer les paramètres de la requête
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

    // Convertir les paramètres en JSON string
    const paramsJson = JSON.stringify(params);

    // Lancer le script Python
    const pythonProcess = spawn('python', [
      path.join(__dirname, './Python/volatility.py'),
      paramsJson
    ]);

    let dataString = '';

    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      throw new Error(`Python Error: ${data}`);
    });

    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Process exited with code ${code}`));
        } else {
          resolve();
        }
      });
    });

    try {
      const result = JSON.parse(dataString);
      res.json(result);
    } catch (e) {
      res.status(500).json({ 
        error: 'Invalid Python output',
        message: e.toString()
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

exports.getVolatilityData_svi = async (req, res) => {
  try {
    // Récupérer les paramètres de la requête
    const params = {
      fwd: parseFloat(req.query.fwd || 1.0),
      time: parseFloat(req.query.time || 0.333),
      b: parseFloat(req.query.b || 0.1),
      m: parseFloat(req.query.m || 0.01),
      sigma: parseFloat(req.query.sigma || 0.4)
    };

    // Convertir les paramètres en JSON string
    const paramsJson = JSON.stringify(params);

    // Lancer le script Python
    const pythonProcess = spawn('python', [
      path.join(__dirname, './Python/volatility_svi.py'),
      paramsJson
    ]);

    let dataString = '';

    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      throw new Error(`Python Error: ${data}`);
    });

    await new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Process exited with code ${code}`));
        } else {
          resolve();
        }
      });
    });

    try {
      const result = JSON.parse(dataString);
      res.json(result);
    } catch (e) {
      res.status(500).json({ 
        error: 'Invalid Python output',
        message: e.toString()
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

// Add this to AnalyticalSigmaVolatilityCalibration.js
