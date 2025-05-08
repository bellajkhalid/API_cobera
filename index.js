'use strict';

const path = require('path');
const http = require('http');
const express = require('express');
const oas3Tools = require('oas3-tools');
const { CONFIG } = require('./service/config');
const setupMiddleware = require('./middleware');
const uiRoutes = require('./routes');

const serverPort = 5001;
const Host = 'localhost';

// Create Express application
const app = express();

// Setup all middleware
setupMiddleware(app);

// Swagger configuration with standard validation
const options = {
    routing: {
        controllers: path.join(__dirname, './controllers')
    }
};

// Create Swagger middleware
const swaggerMiddleware = oas3Tools.expressAppConfig(path.join(__dirname, 'api/openapi.yaml'), options);
const swaggerApp = swaggerMiddleware.getApp();

// Log Python configuration
console.log('Python Configuration:');
console.log(' - Executable:', CONFIG.PYTHON.EXECUTABLE);
console.log(' - Site Packages:', CONFIG.PYTHON.SITE_PACKAGES);
console.log(' - Service Path:', CONFIG.PYTHON.PYTHON_SERVICE_PATH);
console.log(' - Common Path:', CONFIG.PYTHON.PYTHON_COMMON_PATH);
console.log(' - Module Path:', CONFIG.PYTHON.XSIGMA_MODULE_PATH);

// Register UI routes
app.use(uiRoutes);

// Integrate Swagger routes after UI routes
app.use(swaggerApp);

// Start server
http.createServer(app).listen(serverPort, Host, function () {
    console.log('Your server is listening on port %d', serverPort);
    console.log('Swagger-ui is available on http://%s:%d/docs', Host, serverPort);
    console.log('Main application: http://%s:%d/docs', Host, serverPort);
    console.log('SVI Visualization: http://%s:%d/svi', Host, serverPort);
    console.log('ZABR Visualization: http://%s:%d/zabr', Host, serverPort);
});
