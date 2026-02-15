# KACU React Client

A simple React client to interact with the KACU backend API.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
   - Edit `.env` file to set your backend URL
   - Default: `VITE_BACKEND_URL=https://kacu-backend.onrender.com`

3. Start development server:
```bash
npm run dev
```

4. Open browser at `http://localhost:3000`

## Features

- Fetches active loan types from the backend API
- Displays API response in a formatted view
- Error handling for failed requests
- Environment-based configuration

## API Endpoint

- **GET** `/api/loan-types/active/` - Fetch active loan types
