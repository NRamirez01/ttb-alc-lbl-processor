# ttb-alc-lbl-processor

A local-first OCR and label review app for TTB alcohol label processing. It extracts text from label images, compares application form values against OCR results, and runs label compliance checks.

## Overview

This project is designed to run primarily on **local compute**.

It can use:

- a local `llama-cpp` server for faster OCR-backed vision processing
- a CPU fallback path when the OCR server is unavailable

The app includes:

- a **FastAPI** backend
- a TypeScript frontend served from `frontend/dist`
- OCR result visualization with annotated image output
- application-vs-label validation checks
- per-image compliance and warning checks

## Why local compute

Using local compute instead of cloud-hosted inference can be useful for:

- **Security and privacy**: label images and extracted text stay on your machine or internal network
- **Air-gapped operation**: local OCR can be run in restricted or disconnected environments
- **Lower recurring cost**: no per-request cloud inference charges
- **Operational control**: you control hardware, upgrades, and deployment timing
- **Multiple model workflows**: multiple local models can run at once for different application needs

For example, one local model can focus on OCR while other local models handle different application workflows.

### Tradeoffs

- local setup can be more complicated
- performance depends on your hardware
- CPU fallback can be significantly slower than local GPU-backed inference
- long CPU OCR requests may time out behind Cloudflare or similar proxies

## Why this uses actual application data

This template for this project is **heavily** inspired by the real COLA application.

It keeps the workflow closer to the real review process that people are already familiar with and lays the groundwork for future workflow optimizations.

Beyond direct COLA integrations, the format is aimed toward being targetted to be compatible with current systems.

## Demo video
Watch the demo here: 
-- [Fast Mode](https://raw.githubusercontent.com/NRamirez01/ttb-alc-lbl-processor/main/docs/Fast_Mode_OCR.mp4)

-- [Quality Mode](https://raw.githubusercontent.com/NRamirez01/ttb-alc-lbl-processor/main/docs/Quality_Mode_OCR.mp4)



## Prerequisites

Recommended:

- Python 3.11+
- Node.js 20+
- npm
- Windows PowerShell, Command Prompt, or a compatible shell

Optional but strongly recommended for faster OCR:

- `llama-server`
- a local GPU-supported setup for `llama.cpp`

## Required model files (for GPU inference)

This app supports local OCR using the PaddleOCR-VL GGUF model files.

Download **both** required files from the PaddleOCR-VL-1.6-GGUF [repository](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6-GGUF):

- the main GGUF model file
- the matching multimodal projector (`mmproj`) file

Place them in the repo’s `models/` folder.

Example:

```text
ttb-alc-lbl-processor/
  models/
    PaddleOCR-VL-1.6-GGUF.gguf
    PaddleOCR-VL-1.6-GGUF-mmproj.gguf
```

If either file is missing, the local OCR server will not work correctly.

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/NRamirez01/ttb-alc-lbl-processor.git
cd ttb-alc-lbl-processor
```

### 2. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```bat
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Build the frontend

```bash
cd frontend
npm run build
cd ..
```

## Start the local OCR server (for GPU inference)

If you want the faster local OCR path, start `llama-server` before launching the app.

Example PowerShell command:

```powershell
llama-server `
  -m ".\models\PaddleOCR-VL-1.6-GGUF.gguf" `
  --mmproj ".\models\PaddleOCR-VL-1.6-GGUF-mmproj.gguf" `
  --host 0.0.0.0 `
  --port 8080 `
  --temp 0 `
  --n-gpu-layers 999 `
  --ctx-size 32768 `
  --parallel 2
```

The backend expects the OCR server at:

```text
http://localhost:8080
```

## Start the app

Run the FastAPI app:

```bash
python -m app.main
```

The app will be available at:

```text
http://127.0.0.1:6333
```

## Health checks

### Backend health

Open:

```text
http://127.0.0.1:6333/health
```

Expected response:

```json
{"status":"ok"}
```

### OCR server health

If your OCR server exposes a health endpoint, test it at:

```text
http://localhost:8080/health
```

If it does not, verify it is listening on port `8080` another way.

## How to use the app

**Manual entry:** Fill out the application form, upload one or more label images, optionally choose an OCR preset, then click **Submit Application** to review OCR, validation, and compliance results.

**TTB URL workflow:** Go to `https://ttbonline.gov/colasonline/publicPageBasicCola.do`, find an application, open its **printable version**, copy the full browser URL, paste it into the **Paste TTB application URL** field, click **load application**, then review and submit.

## OCR backend behavior

The app prefers the local `llama-cpp-server` OCR backend when it is available.

If the OCR server is not reachable, the app can fall back to CPU-based inference with PaddleOCR.

### Notes

- local `llama-cpp-server` inference is much faster than CPU fallback
- CPU fallback may still work, but can be slow
- slow CPU OCR can cause long-running web requests
- if the app is behind Cloudflare, very long OCR requests may time out

## OCR settings and performance tuning

The default OCR configuration is tuned for higher-quality document extraction and layout handling:

```python
use_doc_orientation_classify=True
use_doc_unwarping=True
use_layout_detection=True
merge_layout_blocks=False
use_ocr_for_image_block=True
format_block_content=False
```

These settings help preserve structure and improve OCR quality for label images, especially when layout, rotation, or mixed content is important.

### Current performance

The current local setup using the quality preset takes roughly **5 seconds per image** and it runs on an **AMD Radeon 7900 XTX with ROCm**. 

This setup works well enough for local use, but inference support and optimization are generally stronger in the NVIDIA CUDA ecosystem, so performance may improve further on more optimized or better-supported inference hardware.

In practical terms:

- the current setup is usable
- it performs well enough for local workflows
- it is upgradeable
- faster inference hardware could reduce processing time significantly

### OCR presets

The app supports multiple OCR presets so you can trade speed for quality.

- **Fast**: prioritizes speed and is roughly **about twice as fast**, but may reduce OCR quality or layout fidelity
- **Balanced**: a middle-ground option
- **Quality**: prioritizes better OCR quality and structure, but may be slower

The downside of **Fast** shows up more clearly on more complicated labels.

This would especially noticeable for labels that are:

- photographed at unusual angles
- affected by poor lighting
- affected by glare on the bottle
- showing sideways text

An example of a more challenging real-world application for OCR is:

```text
https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicFormDisplay&ttbid=16199001000074
```

In cases like that, the **Quality** preset is more reliable than **Fast** as the latter is just not able to pick up a lot of the text.

**NOTE** Presets do not effect the CPU inference pipeline settings as the processing time hit is too large.

### Speed vs quality toggles

Presets work through changing the OCR pipeline instantiation settings.
Relevant options include:

```python
use_doc_orientation_classify=True
use_doc_unwarping=True
use_layout_detection=True
merge_layout_blocks=False
use_ocr_for_image_block=True
format_block_content=False
```

Speed can often be improved by reducing or disabling features such as:

- `use_doc_orientation_classify`
- `use_doc_unwarping`
- `use_layout_detection`
- `use_ocr_for_image_block`

However, those changes may reduce extraction quality depending on the label image.

If speed matters more than OCR quality, use **Fast**.
If OCR quality matters more than speed, use **Quality**.

## Output behavior

The app may create or use these directories during processing:

- `models/` for local model files
- `output/` for generated annotated images
- `tmp/` for temporary uploads or transient processing files
- `static/uploads/` for uploaded source images if persisted for preview/results rendering

Example `.gitignore` patterns:

```gitignore
output/*
!output/.gitkeep

tmp/*
!tmp/.gitkeep

models/*
!models/.gitkeep

static/uploads/*
!static/uploads/.gitkeep
```

## Troubleshooting

### Backend health works but OCR is very slow

The app is likely using CPU fallback because the OCR server is not available.

Check:

- is `llama-server` running?
- is it listening on `http://localhost:8080`?
- are both required model files present in `models/`?
- did the server start successfully with the correct `--mmproj` path?

### Cloudflare returns a timeout

If this app is exposed through Cloudflare and OCR falls back to CPU, long-running requests may exceed proxy time limits.

If that happens:

- start the local OCR server for faster inference
- reduce request size or batch size
- use the **Fast** OCR preset
- consider background job processing for long OCR jobs

### Uploaded image OCR works but the image preview is missing in results

This usually means the uploaded image was processed in memory for OCR, but the original file was not persisted to a browser-accessible static path such as `static/uploads/`.

### Frontend changes do not appear

Rebuild the frontend:

```bash
cd frontend
npm run build
cd ..
```

Then restart the backend.

### OCR server fails to start

Verify:

- the GGUF model file path is correct
- the `mmproj` file path is correct
- port `8080` is not already in use
- your local hardware/runtime supports the `llama-server` configuration you chose

### Application starts but the root page is blank or missing

The backend serves the frontend only if the built frontend exists.

Make sure `frontend/dist` has been generated.

## Summary

To run this app successfully, the most important things are:

- install Python dependencies
- install and build the frontend
- place both OCR model files in `models/`
- start `llama-server` on `http://localhost:8080` for faster OCR
- run the FastAPI app on `http://127.0.0.1:6333`

If `llama-server` is unavailable, CPU fallback may still work, but it can be much slower.
