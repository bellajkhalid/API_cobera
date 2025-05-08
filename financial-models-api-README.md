# Financial Models API

A comprehensive API for advanced financial modeling with volatility surfaces and interest rate models.

## Features

- **SVI**: Stochastic Volatility Inspired models
- **ZABR**: Zero Correlation SABR models with various implementations
- **ASV**: Analytical Sigma Volatility models
- **HJM**: Heath-Jarrow-Morton interest rate models
- **Interactive Visualizations**: Web-based visualizations for model outputs

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- Python 3.11 or higher
- Required Python packages (see Python requirements)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/financial-models-api.git
   cd financial-models-api
   ```

2. Install Node.js dependencies:
   ```
   npm install
   ```

3. Configure the Python environment:
   - Ensure Python is installed and accessible
   - Set up the required Python environment variables in `.env` file

4. Start the server:
   ```
   npm start
   ```

5. Access the application:
   - Main application: http://localhost:5001
   - API documentation: http://localhost:5001/docs
   - SVI Visualization: http://localhost:5001/svi
   - ZABR Visualization: http://localhost:5001/zabr

## Configuration

The application can be configured using environment variables or the `.env` file in the `config` directory:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | 5001 |
| `PYTHON_EXECUTABLE` | Path to Python executable | Platform-specific |
| `PYTHONPATH` | Python module search path | Platform-specific |
| `XSIGMA_DATA_ROOT` | Root directory for data files | Platform-specific |
| `PYTHON_TIMEOUT_MS` | Timeout for Python processes (ms) | 30000 |

## Project Structure

```
financial-models-api/
│
├── config/                         # Configuration files
│   ├── app-config.js               # Main application configuration
│   ├── python-config.js            # Python integration configuration
│   └── .env                        # Environment variables
│
├── src/                            # Source code
│   ├── api/                        # API definition and documentation
│   ├── controllers/                # API controllers
│   ├── services/                   # Business logic services
│   │   ├── models/                 # Model implementations
│   │   └── python/                 # Python integration
│   ├── middleware/                 # Express middleware
│   ├── utils/                      # Utility functions
│   └── routes/                     # Express routes
│
├── public/                         # Static assets
│
├── views/                          # UI templates
│
├── tests/                          # Tests
│
├── scripts/                        # Utility scripts
│
├── docs/                           # Documentation
│
├── index.js                        # Application entry point
└── package.json                    # NPM package configuration
```

## API Documentation

The API is documented using OpenAPI 3.0. You can access the Swagger UI at http://localhost:5001/docs when the server is running.

### Available Endpoints

- `/AnalyticalSigmaVolatilityCalibration` - Calibrate volatility models
- `/api/hjm` - Get HJM calibration results
- `/api/zabr_calibration` - Get ZABR calibration results
- `/api/zabr/classical` - Get Classical ZABR model results
- `/api/zabr/mixture` - Get Mixture ZABR model results
- `/api/zabr/pde` - Get PDE SABR model results
- `/api/Lognormal_FX_With_MHJM_Rates` - Get HJM calibration results with lognormal FX rates

## Visualizations

The application provides web-based visualizations for the financial models:

- **SVI Visualization**: http://localhost:5001/svi
- **ZABR Visualization**: http://localhost:5001/zabr
  - Classical ZABR: http://localhost:5001/zabr/classical
  - Mixture ZABR: http://localhost:5001/zabr/mixture

## Python Integration

The application integrates with Python for complex financial calculations. The Python code is organized in the `src/services/python/models` directory:

- `common/` - Shared Python utilities
- `fx/` - FX models
- `interest-rate/` - Interest rate models
- `volatility/` - Volatility models

## Development

### Running in Development Mode

```
npm run dev
```

This will start the server with nodemon, which will automatically restart when files are changed.

### Testing

```
npm test
```

### Python Integration Testing

```
node scripts/test-python-integration.js
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the ISC License - see the LICENSE file for details.

## Acknowledgments

- [Express](https://expressjs.com/) - Web framework
- [oas3-tools](https://github.com/oas-tools/oas3-tools) - OpenAPI integration
- [Plotly.js](https://plotly.com/javascript/) - Visualization library
