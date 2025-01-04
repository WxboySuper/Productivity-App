const log = require('electron-log');
const path = require('path');
const { app } = require('electron');

// Initialize base logging
log.initialize();

// Get logs directory path
function getLogPath() {
    try {
        // Ensure we're using an absolute path for logs
        const basePath = process.type === 'browser' && app?.isReady() 
            ? app.getPath('userData')
            : path.resolve(process.cwd());
            
        const logPath = path.join(basePath, 'logs');
        
        // Ensure the logs directory exists
        if (!require('fs').existsSync(logPath)) {
            require('fs').mkdirSync(logPath, { recursive: true });
        }
        
        return logPath;
    } catch (error) {
        console.error('Error setting up log path:', error);
        return path.join(process.cwd(), 'logs');
    }
}

// Configure logging after initialization
function configureLogging() {
    const LOG_PATH = getLogPath();
    
    // Set log levels based on environment
    const level = process.env.NODE_ENV === 'development' ? 'debug' : 'info';

    // Configure file transport
    if (log.transports.file) {
        log.transports.file.level = level;
        log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {category} - {text}';
        log.transports.file.maxSize = 10 * 1024 * 1024; // 10MB
        log.transports.file.resolvePathFn = () => path.join(LOG_PATH, 'productivity.log'); // Updated to use resolvePathFn
    }

    // Configure console transport
    if (log.transports.console) {
        log.transports.console.level = level;
        log.transports.console.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}';
    }
}

// Initial configuration
configureLogging();

// Reconfigure logging when app is ready (in main process)
if (process.type === 'browser' && app && !app.isReady()) {
    app.whenReady().then(() => {
        configureLogging();
    });
}

const generateRequestId = () => {
    const { v4: uuidv4 } = require('uuid');
    return uuidv4();
};

// Structured logging helper
const logOperation = (type, operation, details = {}, error = null) => {
    // Normalize log type and validate
    const validTypes = ['debug', 'info', 'warn', 'error'];
    let logType = type.toLowerCase();
    
    if (!validTypes.includes(logType)) {
        console.warn(`Invalid log type: ${type}, defaulting to info`);
        logType = 'info';
    }

    const logData = {
        requestId: generateRequestId(),
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

    const logMessage = JSON.stringify(logData);

    switch (logType) {
        case 'debug':
            log.debug(logMessage);
            break;
        case 'info':
            log.info(logMessage);
            break;
        case 'warn':
            log.warn(logMessage);
            break;
        case 'error':
            log.error(logMessage);
            break;
        default:
            log.warn(`Unexpected log type: ${logType}`);
            log.info(logMessage);
            break;
    }
};

module.exports = {
    log,
    logOperation,
    generateRequestId
};
