# Installation Instructions for PropVision-AI

## Step 1: Activate Virtual Environment

### Windows (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows (CMD)
```cmd
.venv\Scripts\activate.bat
```

### Linux/Mac
```bash
source .venv/bin/activate
```

## Step 2: Install PyTorch (Choose based on your system)

### For CUDA 11.8 (NVIDIA GPU)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### For CUDA 12.1 (NVIDIA GPU - Latest)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### For CPU Only
```bash
pip install torch torchvision torchaudio
```

## Step 3: Install All Other Dependencies
```bash
pip install -r requirements.txt
```

## Step 4: Verify Installation
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
```

## Quick Setup (All-in-One)

### Windows PowerShell
```powershell
# Create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install PyTorch (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -r requirements.txt
```

### Linux/Mac
```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate

# Install PyTorch
pip install torch torchvision torchaudio

# Install other dependencies
pip install -r requirements.txt
```
