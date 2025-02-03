'use strict';

const path = require('path');
const fs = require('fs').promises;
const { spawn } = require('child_process');

// Configuration constants with increased timeout
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
  TIMEOUT_MS: 1200000  // Increased to 1200 seconds
};

class PythonExecutionError extends Error {
  constructor(message, status = 500, details = {}) {
    super(message);
    this.name = 'PythonExecutionError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Validates the Python script existence and permissions
 */
async function validatePythonScript(scriptPath) {
  try {
    await fs.access(scriptPath, fs.constants.R_OK);
  } catch (error) {
    throw new PythonExecutionError(
      `Python script not found or not readable at: ${scriptPath}`,
      500,
      { scriptPath, error: error.message }
    );
  }
}

/**
 * Creates Python execution environment
 */
function createPythonEnvironment(scriptDir) {
  return {
    ...process.env,
    PYTHONPATH: PYTHON_CONFIG.SITE_PACKAGES,
    XSIGMA_DATA_ROOT: PYTHON_CONFIG.DATA_ROOT,
    PYTHONUNBUFFERED: '1'
  };
}

/**
 * Executes Python process with the given arguments
 */
function executePythonProcess(pythonPath, args, env) {
  const process = spawn(pythonPath, args, {
    env,
    cwd: path.dirname(args[0]),
    stdio: ['pipe', 'pipe', 'pipe']
  });

  const output = { stdout: '', stderr: '' };

  process.stdout.on('data', (data) => {
    const str = data.toString();
    console.log('[Python stdout]:', str);
    output.stdout += str;
  });

  process.stderr.on('data', (data) => {
    const str = data.toString();
    console.error('[Python stderr]:', str);
    output.stderr += str;
  });

  return { process, output };
}

function parseJsonOutput(output) {
  const jsonMatch = output.match(/\{[\s\S]*\}/g);
  if (!jsonMatch) {
    throw new PythonExecutionError('No valid JSON found in output', 500, { output });
  }
  
  try {
    return JSON.parse(jsonMatch[jsonMatch.length - 1]);
  } catch (error) {
    throw new PythonExecutionError(
      'Failed to parse Python output',
      500,
      { error: error.message, rawOutput: output }
    );
  }
}

/**
 * Handle requests for the LognormalFXWithMHJMRates service
 */
exports.LognormalFXWithMHJMRates = async function(req, res) {
  try {
    console.log('Computing HJM calibration with params:', req.query);

    // Set up paths
    const projectRoot = path.resolve(__dirname, '..');
    const pythonScriptPath = path.join(
      projectRoot,
      'service',
      'Python',
      'LognormalFXWithMHJMRates.py'
    );

    // Validate script existence
    await validatePythonScript(pythonScriptPath);

    // Prepare command line arguments
    const args = [pythonScriptPath];
    if (req.query.num_paths) {
      args.push('--num-paths', req.query.num_paths);
    }
    if (req.query.volatility) {
      args.push('--volatility', req.query.volatility);
    }

    // Log execution details
    console.log('[Configuration]', {
      pythonExecutable: PYTHON_CONFIG.EXECUTABLE,
      scriptPath: pythonScriptPath,
      pythonPath: PYTHON_CONFIG.SITE_PACKAGES,
      workingDirectory: path.dirname(pythonScriptPath),
      arguments: args
    });

    // Set up and execute Python process
    const env = createPythonEnvironment(path.dirname(pythonScriptPath));
    const { process: pythonProcess, output } = executePythonProcess(
      PYTHON_CONFIG.EXECUTABLE,
      args,
      env
    );

    // Handle process completion with increased timeout
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        reject(new PythonExecutionError(
          `Python process timed out after ${PYTHON_CONFIG.TIMEOUT_MS}ms`,
          500
        ));
      }, PYTHON_CONFIG.TIMEOUT_MS);

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        console.log('[Python process] exited with code:', code);
        
        if (code !== 0) {
          reject(new PythonExecutionError(
            `Python process exited with code ${code}`,
            500,
            { stderr: output.stderr }
          ));
        } else {
          resolve();
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        console.error('[Python process] failed to start:', error);
        reject(new PythonExecutionError(
          'Failed to start Python process',
          500,
          { error: error.message }
        ));
      });
    });

    // Parse and validate results
    const result = parseJsonOutput(output.stdout);
    
    // Return results
    return res.json(result);

  } catch (error) {
    // Ensure consistent error format
    console.error('[Error]', error);
    const statusCode = error instanceof PythonExecutionError ? error.status : 500;
    res.status(statusCode).json({
      status: 'error',
      data: null,
      error: error.message
    });
  }
};