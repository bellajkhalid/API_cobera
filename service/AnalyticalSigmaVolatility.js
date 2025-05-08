'use strict';

const path = require('path');
const { spawn } = require('child_process');

const XSIGMA_PYTHON = process.env.XSIGMA_PYTHON || 'C:/dev/build_ninja_avx2_python_sphinx/bin/xsigmapython.exe';
const PYTHONPATH = process.env.PYTHONPATH || 'C:/dev/build_ninja_avx2_python/lib/python3.12/site-packages';
const XSIGMA_DATA_ROOT = process.env.XSIGMA_DATA_ROOT || 'C:/dev/build_ninja_avx2_python/ExternalData/Testing';

const DEFAULT_PARAMS = {
  1: {
    fwd: 2245.0656707892695,
    time: 1.0,
    ctrl_p: 0.2,
    ctrl_c: 0.2,
    atm: 1.1,
    skew: 3.5,
    smile: 17,
    put: 0.7,
    call: 0.06
  },
  default: {
    fwd: 1.0,
    time: 0.333,
    ctrl_p: 0.2,
    ctrl_c: 0.2,
    atm: 0.1929,
    skew: 0.02268,
    smile: 0.00317,
    put: -0.00213,
    call: -0.00006
  }
};

exports.getAnalyticalSigmaVolatility = async function(req, res) {
  try {
    const test = parseInt(req.query.Test || '1');
    const defaultSet = DEFAULT_PARAMS[test] || DEFAULT_PARAMS.default;

    const params = {
      n: parseInt(req.query.n || '200'),
      fwd: parseFloat(req.query.fwd || defaultSet.fwd),
      time: parseFloat(req.query.time || defaultSet.time),
      ctrl_p: parseFloat(req.query.ctrl_p || defaultSet.ctrl_p),
      ctrl_c: parseFloat(req.query.ctrl_c || defaultSet.ctrl_c),
      atm: parseFloat(req.query.atm || defaultSet.atm),
      skew: parseFloat(req.query.skew || defaultSet.skew),
      smile: parseFloat(req.query.smile || defaultSet.smile),
      put: parseFloat(req.query.put || defaultSet.put),
      call: parseFloat(req.query.call || defaultSet.call),
      Test: test
    };

    Object.entries(params).forEach(([key, value]) => {
      if (isNaN(value)) throw new Error(`Invalid value for ${key}`);
    });

    const pythonScriptPath = path.join(__dirname, './Python/AnalyticalSigmaVolatility.py');
    const env = { ...process.env, PYTHONPATH, XSIGMA_DATA_ROOT, PYTHONUNBUFFERED: '1' };
    const args = Object.values(params).map(String);

    const pythonProcess = spawn(XSIGMA_PYTHON, [pythonScriptPath, ...args], {
      env,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let [dataString, errorString] = ['', ''];
    pythonProcess.stdout.on('data', (data) => dataString += data.toString());
    pythonProcess.stderr.on('data', (data) => errorString += data.toString());

    const processPromise = new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        reject(new Error('Process timeout after 30s'));
      }, 30000);

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        if (code !== 0) reject(new Error(`Process exited ${code}: ${errorString}`));
        else resolve();
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to start: ${error.message}`));
      });
    });

    await processPromise;
    res.json(JSON.parse(dataString));

  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({
      status: 'error',
      error: error.toString()
    });
  }
};