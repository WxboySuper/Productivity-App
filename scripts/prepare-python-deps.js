const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const pythonPackagesDir = path.join(__dirname, '..', 'python-packages');

// Create directory if it doesn't exist
if (!fs.existsSync(pythonPackagesDir)) {
    fs.mkdirSync(pythonPackagesDir, { recursive: true });
}

// Install Python packages to the local directory
try {
    console.log('Installing Python dependencies...');
    execSync(`pip install -r requirements.txt --upgrade --target="${pythonPackagesDir}"`, {
        stdio: 'inherit'
    });
} catch (error) {
    console.error('Failed to install Python dependencies:', error);
    process.exit(1);
}
