const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  const proxyOptions = {
    target: 'http://localhost:5000',  // Changed to 5000
    changeOrigin: true,
  };

  app.use('/api', createProxyMiddleware(proxyOptions));
  app.use('/oauth', createProxyMiddleware(proxyOptions));
  app.use('/accounts', createProxyMiddleware(proxyOptions));
  app.use('/sync', createProxyMiddleware(proxyOptions));
  app.use('/status', createProxyMiddleware(proxyOptions));

    // Make sure /setup catches ALL setup routes including nested ones
  app.use('/setup', createProxyMiddleware({
    ...proxyOptions,
    context: ['/setup/**'], // This should catch all nested paths
  }));
};