# Extras

This directory contains two useful utility scripts that didn't fit elsewhere in the project but are handy to have around.

## Files

### `install_docker_nodejs.sh`
A quick setup script for Ubuntu 24.04 that installs Docker and Node.js with all the proper GPG keys and repository configuration.

**Usage:**
```bash
chmod +x install_docker_nodejs.sh
./install_docker_nodejs.sh
```

**Important:** You must log out and log back in after running this script for Docker permissions to take effect.

**What it installs:**
- Git (essential tooling)
- Node.js and npm (optional, can be skipped if you only need Docker)
- Docker CE with all components (docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin)
- Proper user permissions for Docker usage

### `make_nice_pdf.py`
Converts JSON conversation files (like chat exports) into clean, professionally formatted PDFs with proper typography.

**Usage:**
```bash
python3 make_nice_pdf.py input.json output.pdf
```

**Features:**
- Automatically manages its own Python virtual environment
- Uses high-quality system serif fonts (TeX Gyre Termes, DejaVu Serif, etc.)
- Book-like typography with proper leading and justification
- Supports both JSON arrays and NDJSON formats
- Progress reporting for large files
- Clean participant summary and message formatting
- Auto-cleanup of temporary virtual environments

**Requirements:** Python 3.6+ (script handles all other dependencies automatically)

## Why These Are Here

These scripts solve common setup and utility needs:
- **install_docker_nodejs.sh**: Saves time on fresh Ubuntu installs with proper Docker setup
- **make_nice_pdf.py**: Turns conversation data into readable, archival-quality documents

Both prioritize "just working" over configuration complexity.
