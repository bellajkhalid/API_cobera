# Project Reorganization Implementation Script

This document provides step-by-step commands to reorganize the project according to the new structure.

## 1. Create New Directory Structure

```powershell
# Create the new root directory (we'll work in a new directory to avoid disrupting the existing code)
mkdir financial-models-api

# Create main directories
mkdir financial-models-api/config
mkdir financial-models-api/src
mkdir financial-models-api/src/api
mkdir financial-models-api/src/api/examples
mkdir financial-models-api/src/controllers
mkdir financial-models-api/src/services
mkdir financial-models-api/src/services/models
mkdir financial-models-api/src/services/models/fx
mkdir financial-models-api/src/services/models/interest-rate
mkdir financial-models-api/src/services/models/volatility
mkdir financial-models-api/src/services/python
mkdir financial-models-api/src/services/python/models
mkdir financial-models-api/src/services/python/models/common
mkdir financial-models-api/src/services/python/models/fx
mkdir financial-models-api/src/services/python/models/interest-rate
mkdir financial-models-api/src/services/python/models/volatility
mkdir financial-models-api/src/middleware
mkdir financial-models-api/src/utils
mkdir financial-models-api/src/routes
mkdir financial-models-api/public
mkdir financial-models-api/public/css
mkdir financial-models-api/public/js
mkdir financial-models-api/public/images
mkdir financial-models-api/views
mkdir financial-models-api/views/layouts
mkdir financial-models-api/views/partials
mkdir financial-models-api/tests
mkdir financial-models-api/tests/unit
mkdir financial-models-api/tests/integration
mkdir financial-models-api/scripts
mkdir financial-models-api/docs
```

## 2. Copy and Rename Files

### Configuration Files

```powershell
# Copy and rename configuration files
copy service/config.js financial-models-api/config/app-config.js
copy service/.env financial-models-api/config/.env

# Extract Python configuration from config.js to a separate file
# (This will need to be done manually by editing the files)
```

### API Files

```powershell
# Copy OpenAPI specification
copy api/openapi.yaml financial-models-api/src/api/openapi.yaml

# Copy API examples
copy api/examples/* financial-models-api/src/api/examples/
```

### Controller Files

```powershell
# Copy and rename controller files
copy controllers/FXModels.js financial-models-api/src/controllers/fx-controller.js
copy controllers/InterestRateModels.js financial-models-api/src/controllers/interest-rate-controller.js
copy controllers/VolatilityASV.js financial-models-api/src/controllers/volatility-asv-controller.js
copy controllers/VolatilitySVI.js financial-models-api/src/controllers/volatility-svi-controller.js
copy controllers/VolatilityZABR.js financial-models-api/src/controllers/volatility-zabr-controller.js
```

### Service Files

```powershell
# Copy and rename FX model files
copy service/LognormalFXWithMHJMRate.js financial-models-api/src/services/models/fx/lognormal-fx-hjm.js

# Copy and rename interest rate model files
copy service/hjm.js financial-models-api/src/services/models/interest-rate/hjm.js
copy service/HW_distribution.js financial-models-api/src/services/models/interest-rate/hw-distribution.js

# Copy and rename volatility model files
copy service/AnalyticalSigmaVolatility.js financial-models-api/src/services/models/volatility/analytical-sigma.js
copy service/AnalyticalSigmaVolatilityCalibration.js financial-models-api/src/services/models/volatility/analytical-sigma-calibration.js
copy service/volatilityDataSvi.js financial-models-api/src/services/models/volatility/svi.js
copy service/volatility_svi.js financial-models-api/src/services/models/volatility/volatility-svi.js
copy service/zabr_analytics.js financial-models-api/src/services/models/volatility/zabr-analytics.js
copy service/zabr_calibration.js financial-models-api/src/services/models/volatility/zabr-calibration.js
```

### Python Service Files

```powershell
# Create Python executor service (will need to be extracted from existing files)
# This will be done manually

# Copy Python model files
copy service/Python/common/* financial-models-api/src/services/python/models/common/

# Copy and rename Python FX model files
copy service/Python/LognormalFXWithMHJMRates.py financial-models-api/src/services/python/models/fx/lognormal-fx-hjm.py

# Copy and rename Python interest rate model files
copy service/Python/HJM.py financial-models-api/src/services/python/models/interest-rate/hjm.py
copy service/Python/HW_distribution.py financial-models-api/src/services/python/models/interest-rate/hw-distribution.py

# Copy and rename Python volatility model files
copy service/Python/AnalyticalSigmaVolatility.py financial-models-api/src/services/python/models/volatility/analytical-sigma.py
copy service/Python/AnalyticalSigmaVolatilityCalibration.py financial-models-api/src/services/python/models/volatility/analytical-sigma-calibration.py
copy service/Python/volatility.py financial-models-api/src/services/python/models/volatility/volatility.py
copy service/Python/volatility_svi.py financial-models-api/src/services/python/models/volatility/volatility-svi.py
copy service/Python/zabr_analytics.py financial-models-api/src/services/python/models/volatility/zabr-analytics.py
copy service/Python/zabr_calibration.py financial-models-api/src/services/python/models/volatility/zabr-calibration.py
```

### Middleware Files

```powershell
# Copy and rename middleware files
copy middleware.js financial-models-api/src/middleware/index.js
copy service/errorHandler.js financial-models-api/src/middleware/error-handler.js
```

### Route Files

```powershell
# Copy and rename route files
copy routes.js financial-models-api/src/routes/ui-routes.js
# Create API routes file (will need to be extracted from existing files)
# This will be done manually
```

### View Files

```powershell
# Copy view files
copy templates/index.html financial-models-api/views/index.html
copy templates/volatility.html financial-models-api/views/volatility-asv.html
copy templates/volatility_svi.html financial-models-api/views/volatility-svi.html
copy templates/zabr_analytics.html financial-models-api/views/zabr-analytics.html
```

### Test Files

```powershell
# Copy test files
copy test-python-integration.js financial-models-api/tests/integration/python-integration-test.js
```

### Root Files

```powershell
# Copy root files
copy index.js financial-models-api/index.js
copy package.json financial-models-api/package.json
copy package-lock.json financial-models-api/package-lock.json
copy .gitignore financial-models-api/.gitignore
```

## 3. Update File Contents

After copying and renaming files, you'll need to update the import/require paths in all files to reflect the new structure. This will involve:

1. Updating all `require()` statements to point to the new file locations
2. Updating all file path references in the code
3. Updating configuration to reflect the new structure

This step will need to be done manually for each file, as it requires understanding the code and its dependencies.

## 4. Create Documentation

```powershell
# Create README.md with project documentation
# This will be done manually
```

## 5. Test the Application

After completing the reorganization, you should test the application to ensure everything works correctly:

```powershell
cd financial-models-api
npm install
npm start
```

## Important Notes

1. This reorganization should be done in a new directory to avoid disrupting the existing code.
2. Consider using version control (git) to track changes and allow for rollback if needed.
3. Test thoroughly after each major step to catch issues early.
4. Update the OpenAPI specification to reflect any changes to API endpoints.
5. Update any documentation to reflect the new structure.
