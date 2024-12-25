# Productivity App
[![Run all tests](https://github.com/WxboySuper/Productivity-App/actions/workflows/testing.yml/badge.svg)](https://github.com/WxboySuper/Productivity-App/actions/workflows/testing.yml)
[![DeepSource](https://app.deepsource.com/gh/WxboySuper/Productivity-App.svg/?label=active+issues&show_trend=true&token=PqTSZxIszGKL6icxa3lwv3Ra)](https://app.deepsource.com/gh/WxboySuper/Productivity-App/)
[![DeepSource](https://app.deepsource.com/gh/WxboySuper/Productivity-App.svg/?label=code+coverage&show_trend=true&token=PqTSZxIszGKL6icxa3lwv3Ra)](https://app.deepsource.com/gh/WxboySuper/Productivity-App/)

A simple productivity app developed by WeatherboySuper as a fun little project to stay occupied (and sometimes procrastinate (oops)).

## Features

- Task management with priority levels
- Categorize tasks
- Set deadlines
- Add notes to tasks
- Label system for better organization
- Local SQLite database storage
- Cross-platform desktop application

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (Flask)
- Database: SQLite
- Desktop Framework: Electron

## Prerequisites

- Node.js
- Python 3.12+
- pip

## Installation

1. Clone the repository:
```sh
git clone [repository-url]
```

2. Install Node.js dependencies:
```sh
npm install
```

3. Install Python dependencies:
```sh
pip install -r requirements.txt
```

## Running the Application
Start the application in development mode:
```sh
npm start
```

## Building
Create a production build:
```sh
npm run build
```

Create a release build:
```sh
npm run release
```

## Testing
Run the Python test suite:
```sh
coverage run --omit=*/test_* -m unittest discover
```

View test coverage:
```sh
coverage report -m
```

Project Structure
```text
.
└── src/
    ├── python/     # Python backend code
    └── tests/      # Test files
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License


## Author
WeatherboySuper 