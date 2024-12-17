const express = require('express');
const path = require('path');
const app = express();
const port = 8080;
const httpProxy = require("http-proxy");
const { createProxyMiddleware } = require("http-proxy-middleware");

const nginxUrl = "http://nginx1:80";

app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.use(
  '/orders',
  createProxyMiddleware({
    target: nginxUrl,
    changeOrigin: true,
    pathRewrite: {
      '^/orders': '/orders',
    },
    onError: (err, req, res) => {
        console.error('Error while proxying:', err.message);
        res.status(500).send('Proxy error: Could not connect to Nginx');
    },
  })
);

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/`);
});
