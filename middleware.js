'use strict';

const cors = require("cors");
const bodyParser = require('body-parser');
const path = require('path');
const express = require('express');

// Configure all middleware
function setupMiddleware(app) {
    // Parse JSON bodies (increased limit for large model outputs)
    app.use(bodyParser.json({ limit: '10mb' }));
    app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

    // CORS configuration
    const corsOptions = {
        origin: '*',
        methods: "GET,HEAD,PUT,PATCH,POST,DELETE",
        preflightContinue: false,
        optionsSuccessStatus: 204
    };
    app.use(cors(corsOptions));

    // Serve static files
    app.use(express.static(path.join(__dirname, 'public')));

    // Template configuration
    app.set('views', path.join(__dirname, 'templates'));
    app.engine('html', require('ejs').renderFile);
    app.set('view engine', 'html');

    // Global error handling middleware
    app.use((err, req, res, next) => {
        console.error('Global error handler:', err);
        
        const statusCode = err.status || 500;
        const errorResponse = {
            status: 'error',
            error: err.message || 'Internal Server Error',
            errorType: err.name || 'GeneralError',
            timestamp: new Date().toISOString()
        };
        
        // Include detailed error info in development mode
        if (process.env.NODE_ENV === 'development') {
            errorResponse.details = {
                stack: err.stack,
                code: err.code,
                stderr: err.stderr
            };
        }
        
        res.status(statusCode).json(errorResponse);
    });
}

module.exports = setupMiddleware;