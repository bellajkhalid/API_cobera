# Project Reorganization Plan

## Current Structure Issues
- Inconsistent naming conventions (camelCase, snake_case, etc.)
- Mixed responsibilities in some files
- Unclear separation between API, services, and UI components
- Duplicate or similar files (e.g., zabr_analytics.py and zabr_analytics copy.py)
- Configuration spread across multiple files

## New Structure

```
financial-models-api/               # Root directory (renamed from Backend_Xsigma)
│
├── config/                         # Configuration files
│   ├── app-config.js               # Main application configuration
│   ├── python-config.js            # Python integration configuration
│   └── .env                        # Environment variables
│
├── src/                            # Source code
│   ├── api/                        # API definition and documentation
│   │   ├── openapi.yaml            # OpenAPI specification
│   │   └── examples/               # API examples
│   │
│   ├── controllers/                # API controllers
│   │   ├── fx-controller.js        # FX models controller
│   │   ├── interest-rate-controller.js  # Interest rate models controller
│   │   ├── volatility-asv-controller.js # ASV volatility controller
│   │   ├── volatility-svi-controller.js # SVI volatility controller
│   │   └── volatility-zabr-controller.js # ZABR volatility controller
│   │
│   ├── services/                   # Business logic services
│   │   ├── models/                 # Model implementations
│   │   │   ├── fx/                 # FX models
│   │   │   │   └── lognormal-fx-hjm.js
│   │   │   │
│   │   │   ├── interest-rate/      # Interest rate models
│   │   │   │   ├── hjm.js
│   │   │   │   └── hw-distribution.js
│   │   │   │
│   │   │   └── volatility/         # Volatility models
│   │   │       ├── analytical-sigma.js
│   │   │       ├── svi.js
│   │   │       ├── zabr-analytics.js
│   │   │       └── zabr-calibration.js
│   │   │
│   │   └── python/                 # Python integration
│   │       ├── executor.js         # Python execution service
│   │       └── models/             # Python model implementations
│   │           ├── common/         # Shared Python utilities
│   │           ├── fx/             # FX Python models
│   │           ├── interest-rate/  # Interest rate Python models
│   │           └── volatility/     # Volatility Python models
│   │
│   ├── middleware/                 # Express middleware
│   │   ├── error-handler.js        # Error handling middleware
│   │   └── index.js                # Middleware setup
│   │
│   ├── utils/                      # Utility functions
│   │   ├── python-utils.js         # Python-related utilities
│   │   └── validation.js           # Input validation utilities
│   │
│   └── routes/                     # Express routes
│       ├── api-routes.js           # API routes
│       └── ui-routes.js            # UI routes
│
├── public/                         # Static assets
│   ├── css/                        # Stylesheets
│   ├── js/                         # Client-side JavaScript
│   └── images/                     # Images
│
├── views/                          # UI templates (renamed from templates)
│   ├── layouts/                    # Layout templates
│   ├── partials/                   # Partial templates
│   ├── volatility-asv.html         # ASV visualization
│   ├── volatility-svi.html         # SVI visualization
│   ├── zabr-analytics.html         # ZABR visualization
│   └── index.html                  # Main landing page
│
├── tests/                          # Tests
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── python-integration-test.js  # Python integration tests
│
├── scripts/                        # Utility scripts
│   └── test-python-integration.js  # Script to test Python integration
│
├── docs/                           # Documentation
│   └── README.md                   # Project documentation
│
├── .gitignore                      # Git ignore file
├── index.js                        # Application entry point
├── package.json                    # NPM package configuration
└── package-lock.json               # NPM package lock
```

## File Naming Conventions

1. **Use kebab-case for file and directory names**:
   - `analytical-sigma.js` instead of `AnalyticalSigmaVolatility.js`
   - `volatility-svi.html` instead of `volatility_svi.html`

2. **Use descriptive, consistent names**:
   - `fx-controller.js` instead of `FXModels.js`
   - `interest-rate-controller.js` instead of `InterestRateModels.js`

3. **Group related functionality**:
   - All volatility models under `services/models/volatility/`
   - All Python models under `services/python/models/`

4. **Separate configuration**:
   - Move all configuration to `config/` directory
   - Centralize Python configuration in `config/python-config.js`

## Implementation Steps

1. Create the new directory structure
2. Move and rename files according to the new structure
3. Update import/require paths in all files
4. Update references to file paths in the code
5. Test the application to ensure everything works correctly

## Benefits of the New Structure

1. **Improved organization**: Clear separation of concerns
2. **Better maintainability**: Related code is grouped together
3. **Consistent naming**: Makes it easier to find files
4. **Scalability**: Structure can accommodate new features
5. **Clarity**: Clear distinction between frontend and backend code
