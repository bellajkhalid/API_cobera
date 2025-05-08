'use strict';

const express = require('express');
const router = express.Router();

router.get('/svi', (req, res) => {
    res.render('volatility_svi');
});

router.get('/zabr', (req, res) => {
    res.render('zabr_analytics');
});

// Add model-specific routes for UI pages
router.get('/zabr/classical', (req, res) => {
    res.render('zabr_analytics', { 
        modelType: 'classical',
        title: 'Classical ZABR Model'
    });
});

router.get('/zabr/mixture', (req, res) => {
    res.render('zabr_analytics', { 
        modelType: 'mixture',
        title: 'Mixture ZABR Model'
    });
});

router.get('/zabr/pde', (req, res) => {
    res.render('zabr_analytics', { 
        modelType: 'pde',
        title: 'PDE ZABR Model'
    });
});

module.exports = router;