name: Build Desktop Pet

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:
  release:
    types: [created]

permissions:
  contents: write

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller pillow requests certifi
    
    - name: Generate spec file
      run: |
        python -c "import certifi; print(f'Certifi location: {certifi.where()}')"
        
    - name: Build EXE with SSL support
      run: |
        pyinstaller DesktopPet.spec
    
    - name: Upload build artifact
      uses: actions/upload-artifact@v4
      with:
        name: DesktopPet-Windows
        path: dist/DesktopPet.exe
        retention-days: 30
    
    - name: Upload to Release (only on release)
      if: github.event_name == 'release'
      uses: softprops/action-gh-release@v1
      with:
        files: dist/DesktopPet.exe
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
