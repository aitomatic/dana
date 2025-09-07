# Quick Ollama Setup for Dana

## Why Use Local Model?
- **Free**: No API costs
- **Fast**: No network delays
- **Private**: Data stays on your machine

## Prerequisites
- 8GB+ RAM
- Dana installed

## Complete Setup (All in One Terminal)

### Step 1: Install Ollama
```bash
pip install ollama
```

### Step 2: Start Ollama Server
```bash
ollama serve
```
*Keep this terminal open - Ollama is now running in the background*

### Step 3: Download a Model (New Terminal)
Open a **new terminal window** and run:
```bash
# Download a fast, lightweight model (~2GB)
ollama pull phi3:mini

# Alternative models you can try:
# ollama pull llama3.2      # Latest, most capable (~4GB)
# ollama pull codellama:7b  # Good for coding (~4GB)
# ollama pull qwen:4b       # Multilingual, efficient (~2.5GB)
# ollama pull gemma:2b      # Very lightweight (~1.5GB)
```

### Step 4: Create .env File
Create a `.env` file in your Dana project directory:
```bash
# Create .env file
echo "LOCAL_BASE_URL=http://localhost:11434/v1" > .env
echo "LOCAL_MODEL_NAME=phi3:mini" >> .env
```

Or manually create `.env` with:
```
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL_NAME=phi3:mini
```

### Step 5: Start Dana REPL
```bash
dana-repl
```

### Step 6: Set Model in Dana
```dana
set_model("local")
```
*This uses the model specified in your .env file*

### Step 7: Test
```dana
agent Neo
Neo.chat("Hello, what's your name?")
```

That's it! 🎉

## Common Issues

**"Connection refused"**
```bash
ollama serve
```

**"Model not found"**
```bash
ollama pull phi3:mini
```

**Out of memory**
- Use `phi3:mini` instead of larger models
- Close other apps

## Other Models

```bash
# List available models
ollama list

# Try different models
ollama pull llama3
ollama pull codellama:7b
```

## Switch Models

**Best Practice:** Update your `.env` file instead of changing Dana code:

```bash
# Edit .env file to change model
LOCAL_MODEL_NAME=llama3.2    # Switch to Llama 3.2
# LOCAL_MODEL_NAME=phi3:mini  # Switch back to Phi-3 Mini
```

Then restart Dana REPL:
```bash
dana-repl
set_model("local")  # Always use "local"
```

## Now, your local model is ready for Dana agent development!