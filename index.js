'use strict';

const path = require('path');
const http = require('http');
const cors = require("cors");
const express = require('express');
const oas3Tools = require('oas3-tools');

const serverPort = 5000;
const Port = 'localhost';

// Créer l'application Express
const app = express();

// Configuration swagger
const options = {
    routing: {
        controllers: path.join(__dirname, './controllers')
    },
};

// Créer le middleware Swagger
const swaggerMiddleware = oas3Tools.expressAppConfig(path.join(__dirname, 'api/openapi.yaml'), options);
const swaggerApp = swaggerMiddleware.getApp();

// Configuration CORS
const corsOptions = {
    origin: '*',
    optionsSuccessStatus: 200
};
app.use(cors(corsOptions));

// Configuration des templates
app.set('views', path.join(__dirname, 'templates'));
app.engine('html', require('ejs').renderFile);
app.set('view engine', 'html');

// Route principale pour servir index_interactive.html
app.get('/', (req, res) => {
    res.render('volatility_svi');
});

// Intégrer les routes Swagger après la route principale
app.use(swaggerApp);

// Démarrer le serveur
http.createServer(app).listen(serverPort, Port, function () {
    console.log(`Server started on port ${serverPort}`);
    console.log(`Swagger UI available at http://${Port}:${serverPort}/docs`);
    console.log(`Application available at http://${Port}:${serverPort}`);
});