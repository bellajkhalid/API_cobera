'use strict';

const path = require('path');
const http = require('http');
const cors = require("cors");
const express = require('express');
const oas3Tools = require('oas3-tools');

const serverPort = 5000;
const Port = 'localhost';

// Create Express application
const app = express();

// Swagger configuration
const options = {
    routing: {
        controllers: path.join(__dirname, './controllers')
    },
};

// Create Swagger middleware
const swaggerMiddleware = oas3Tools.expressAppConfig(path.join(__dirname, 'api/openapi.yaml'), options);
const swaggerApp = swaggerMiddleware.getApp();

// CORS configuration
const corsOptions = {
    origin: '*',
    optionsSuccessStatus: 200
};
app.use(cors(corsOptions));

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Template configuration
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', require('ejs').renderFile);
app.set('view engine', 'html');

// Main routes
app.get('/', (req, res) => {
    res.render('index');  // Main landing page
});

app.get('/svi', (req, res) => {
    res.render('volatility_svi');
});

app.get('/zabr', (req, res) => {
    res.render('zabr_analytics');
});

// Add model-specific routes
app.get('/zabr/classical', (req, res) => {
    res.render('zabr_analytics', { 
        modelType: 'classical',
        title: 'Classical ZABR Model'
    });
});

app.get('/zabr/mixture', (req, res) => {
    res.render('zabr_analytics', { 
        modelType: 'mixture',
        title: 'Mixture ZABR Model'
    });
});

app.get('/zabr/pde', (req, res) => {
    res.render('zabr_analytics', { 
        modelType: 'pde',
        title: 'PDE ZABR Model'
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        status: 'error',
        message: 'Internal Server Error',
        error: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// Integrate Swagger routes after main routes
app.use(swaggerApp);

// Start server
http.createServer(app).listen(serverPort, Port, function () {
    console.log('Your server is listening on port %d', serverPort);
    console.log('Swagger-ui is available on http://%s:%d/docs', Port, serverPort);
    console.log('Main application: http://%s:%d', Port, serverPort);
    console.log('SVI Visualization: http://%s:%d/svi', Port, serverPort);
    console.log('ZABR Visualization: http://%s:%d/zabr', Port, serverPort);
    console.log('ZABR Classical Model: http://%s:%d/zabr/classical', Port, serverPort);
    console.log('ZABR Mixture Model: http://%s:%d/zabr/mixture', Port, serverPort);
    console.log('ZABR PDE Model: http://%s:%d/zabr/pde', Port, serverPort);
});