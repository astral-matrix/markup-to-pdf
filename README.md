# Markdown to PDF Converter

A full-stack web application that converts Markdown to beautifully styled PDFs with customizable typography and layout options.

## Purpose

This application was created to generate high-quality PDFs from ChatGPT responses. Simply:

1. Copy any ChatGPT response using ChatGPT's built-in copy button (which copies the markdown format)
2. Paste the markdown text into the input box
3. Customize the typography and layout options
4. Generate and download a professionally formatted PDF

The app works by preserving all markdown formatting from ChatGPT responses, including code blocks, tables, lists, and other formatting elements. The backend processes the markdown using Python's markdown library with extensions for enhanced features like syntax highlighting, then converts it to PDF using a combination of HTML rendering and PDF generation libraries.

## Project Structure

This is a monorepo containing:

- `markup2pdf-backend`: FastAPI Python service for Markdown-to-PDF conversion
- `markup2pdf-webapp`: Next.js frontend for the web application

## Features

- Convert CommonMark + GitHub-style Markdown to styled PDFs
- Customize font family and size
- Layout options including spacing and table width control
- Fast PDF generation (< 1s for average documents)
- Accessibility tagging for screen readers

## Technology Stack

| Layer      | Technologies Used                                       |
| ---------- | ------------------------------------------------------- |
| Frontend   | Next.js, React, TypeScript, TailwindCSS, TanStack Query |
| Backend    | Python, FastAPI, Uvicorn, Pydantic                      |
| PDF Engine | ReportLab (primary), WeasyPrint (fallback)              |
| Markdown   | markdown-it-py with table and highlight plugins         |

## Prerequisites

This project has been tested with the following runtime versions:

- **Node.js** 22.x
- **Python** 3.11

## Quick Start

For convenience, an ENV install script is provided:
"install.sh" installs and configure the frontend and backend ENVs and imports.

NOTE: the "start.sh" script will launch both the backend and frontend services in the background, but processes will have to be manually killed. Thus this script is NOT RECOMMENDED. Instead, to keep things simple, run the python server start command and node server start commands in separate terminal windows.

1. Make sure the install script is executable:

   ```
   chmod +x install.sh
   ```

2. Run the ENV install and configuration script:
   ```
   ./install.sh
   ```
   This will:

- Install and activate the Python virtual environment
- Install all Python dependencies
- Install all the Node.js dependencies

3. Run the server start commands (from Project Home directory):
   Python Server:

   ```
   cd markup2pdf-backend
   python3 run.py
   ```

   Node.js Web Server:

   ```
   cd markup2pdf-webapp
   npm run dev
   ```

This will:

- Start the Python backend server
- Start the frontend development web server
- Web app URL: http://localhost:3000

## Getting Started - Python ENV (MANUAL SETUP)

### Backend Setup

1. Navigate to the backend directory:

   ```
   cd markup2pdf-backend
   ```

2. Create a virtual environment (dir: markup2pdf-backend/ ):

   ```
   python3 -m venv .venv
   ```

3. Activate the virtual environment (dir: markup2pdf-backend/ ):

   ```
   # On macOS/Linux
   source .venv/bin/activate

   # On Windows
   .venv\Scripts\activate
   ```

4. Install dependencies (dir: markup2pdf-backend/ ):

   ```
   python3 -m pip install -r requirements.txt
   ```

5. Run/ Test the backend server (dir: markup2pdf-backend/ ):

   ```
   python3 run.py
   ```

The backend API will be available at http://localhost:5000.

You can check if the server is running by visiting:

- API documentation: http://localhost:5000/docs
- Health check: http://localhost:5000/health

## Getting started - Node.js ENV setup (MANUAL SETUP)

### Frontend Setup

1. From Project Root, navigate to the frontend directory:

   ```
   cd markup2pdf-webapp
   ```

2. Install dependencies (dir: markup2pdf-webapp/ ) :

   ```
   npm install
   ```

3. Run the development server (dir: markup2pdf-webapp/ ):
   ```
   npm run dev
   ```

The frontend will be available at http://localhost:3000.

## API Endpoints

| Method | Path          | Description                             |
| ------ | ------------- | --------------------------------------- |
| POST   | /generate-pdf | Generates a PDF from markdown content   |
| GET    | /fonts        | Returns list of available font families |

## Project Goals

- **User workflow:** Paste markdown → choose typography options → generate PDF → download
- **Quality:** Output embeds fonts, avoids missing glyphs, wraps table text, supports accessibility tagging
- **Performance:** Fast generation (< 1s for average documents)
- **Reliability:** Well-tested, graceful error handling

## License

MIT
