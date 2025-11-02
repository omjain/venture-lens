# Installation Guide for FastAPI Scoring Service

## Option 1: Quick Install (Recommended)

Install packages one by one to avoid Rust compilation issues:

```bash
cd api
pip install fastapi uvicorn[standard]
pip install pydantic
pip install google-auth google-auth-oauthlib google-auth-httplib2
pip install python-dotenv httpx requests
```

## Option 2: Install Rust (For full compatibility)

If you want to install all packages at once, you'll need Rust:

1. **Install Rust**: https://rustup.rs/
   ```bash
   # On Windows, download and run rustup-init.exe
   # Or use: winget install Rustlang.Rustup
   ```

2. **Then install requirements**:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

## Option 3: Use Pre-built Wheels (Easiest)

Try installing without specifying exact versions to get pre-built wheels:

```bash
cd api
pip install --upgrade pip
pip install fastapi uvicorn[standard] pydantic google-auth python-dotenv httpx requests
```

## Verify Installation

```bash
python -c "import fastapi; print('FastAPI installed successfully')"
```

## Run the Service

After installation:

```bash
cd api
uvicorn main:app --reload --port 8000
```

The service will be available at: http://localhost:8000

## Troubleshooting

### Issue: "pydantic-core requires Rust"
- **Solution**: Install Rust from https://rustup.rs/ or use Option 3 above

### Issue: "google-cloud-aiplatform not found"
- **Solution**: This package is optional. The service uses `google.auth` directly which is already in requirements.

### Issue: Python version
- **Recommendation**: Use Python 3.9-3.11 for best compatibility. Python 3.13 may have compatibility issues with some packages.

