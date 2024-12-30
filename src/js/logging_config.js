const log = require('electron-log');
const path = require('path');

// Configure electron-log
log.transports.file.level = 'info';
log.transports.console.level = 'debug';
log.transports.file.maxSize = 10 * 1024 * 1024; // 10MB
log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}';
log.transports.file.fileName = 'productivity.log';
log.transports.file.resolvePath = () => path.join('logs', 'productivity.log');

// Add request ID tracking
const generateRequestId = () => {
    return 'req_' + Math.random().toString(36).substr(2, 9);
};

// Structured logging helper
const logOperation = (type, operation, details = {}, error = null) => {
    const requestId = generateRequestId();
    const logData = {
        requestId,
        operation,
        timestamp: new Date().toISOString(),
        ...details
    };

    if (error) {
        logData.error = {
            message: error.message,
            stack: error.stack
        };
    }

    switch (type.toLowerCase()) {
        case 'debug':
            log.debug(JSON.stringify(logData));
            break;
        case 'info':
            log.info(JSON.stringify(logData));
            break;
        case 'warn':
            log.warn(JSON.stringify(logData));
            break;
        case 'error':
            log.error(JSON.stringify(logData));
            break;
        default:
            log.warn(`Invalid log type: ${type}`);
            break;
    }

    return requestId;
};

module.exports = {
    log,
    logOperation,
    generateRequestId
};
