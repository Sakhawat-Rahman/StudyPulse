# StudyPulse AI Models Directory

This folder is designed to host optional offline local neural weights and `llama.cpp` CLI binaries for zero-idle-RAM neural task slicing.

## Supported Model
- **Model**: `SmolLM2-360M-Instruct-Q4_K_M.gguf` (~270 MB)
- **Engine**: `llama-cli.exe` / `llama-connect.exe` (Windows x64 with AVX2 support)

## Built-In Fallback
If this directory is left empty, StudyPulse automatically and seamlessly utilizes its high-precision **Smart Multidomain NLP Engine** (embedded in Python), which instantly parses multi-exam prompts, dates, and topics with zero setup and zero dependencies.
