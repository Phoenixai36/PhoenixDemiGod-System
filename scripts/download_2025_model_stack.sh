#!/bin/bash
# Phoenix Hydra 2025 Advanced AI Model Stack Downloader
# Automated download script for the complete 2025 model ecosystem
# Integrated with Phoenix Model Manager

set -euo pipefail

# Compatibility Check for Linux-based environment
if [[ "$OSTYPE" != "linux-gnu"* && "$OSTYPE" != "cygwin" && "$OSTYPE" != "msys" ]]; then
    echo -e "\033[0;31mError: Incompatible Operating System.\033[0m"
    echo -e "\033[1;33mThis script is designed for Linux-based environments and relies on tools like 'podman' and 'systemd'.\033[0m"
    echo -e "\033[1;33mYou appear to be running on a different OS ('$OSTYPE'), which will cause syntax errors.\033[0m"
    echo ""
    echo -e "\033[0;32mRecommended Solution:\033[0m"
    echo "Please run this script within the Windows Subsystem for Linux (WSL)."
    echo "1. Install WSL from your terminal: wsl --install"
    echo "2. Open a WSL terminal and re-run this script from there."
    exit 1
fi

# Check if Python Model Manager is available
PYTHON_MANAGER_AVAILABLE=false
if command -v python3 &> /dev/null; then
    if python3 -c "from src.core.model_manager import model_manager" 2>/dev/null; then
        PYTHON_MANAGER_AVAILABLE=true
        echo -e "\033[0;32m✅ Phoenix Model Manager detected - using integrated approach\033[0m"
    fi
fi

# Default parameters
SKIP_VALIDATION=false
PARALLEL=false
OUTPUT_PATH="models/2025-stack"
MAX_CONCURRENT=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --output-path)
            OUTPUT_PATH="$2"
            shift 2
            ;;
        --max-concurrent)
            MAX_CONCURRENT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-validation    Skip model verification after download"
            echo "  --parallel          Use parallel downloads"
            echo "  --output-path PATH  Set output directory (default: models/2025-stack)"
            echo "  --max-concurrent N  Max concurrent downloads (default: 3)"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🚀 Phoenix Hydra 2025 Model Stack Downloader${NC}"
echo -e "${CYAN}================================================${NC}"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama not found. Please install Ollama first: https://ollama.ai${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_PATH"
echo -e "${GREEN}📁 Created model directory: $OUTPUT_PATH${NC}"

# Phoenix Hydra 2025 Model Stack - Optimized for Local Processing
declare -A MODEL_STACK=(
    ["Reasoning Models (SSM Priority)"]="zamba2:2.7b llama3:8b falcon:7b"
    ["Coding Models (Energy Efficient)"]="deepseek-coder:6.7b codestral:7b qwen2.5-coder:7b starcoder2:7b codegemma:7b"
    ["General LLM Models"]="llama3.2:3b falcon:7b mistral:7b phi3:mini gemma2:2b"
    ["Creative/Multimodal Models"]="phi3:14b nous-hermes2:mixtral-8x7b gemma:7b"
    ["Vision Models (Lightweight)"]="clip llava:7b moondream:1.8b"
    ["Audio/TTS Models"]="whisper:base xtts-v2 bark"
    ["Context Long/RAG Models"]="command-r:35b qwen2.5:72b mixtral:8x22b"
    ["CPU Optimized Models"]="tinyllama:1.1b stablelm2:1.6b rwkv:7b openchat:7b"
    ["SSM/Mamba Models (Phoenix Specialty)"]="mamba:7b mamba:13b state-spaces/mamba-130m state-spaces/mamba-370m"
    ["Biomimetic Agent Models"]="neural-chat:7b orca-mini:3b vicuna:7b alpaca:7b"
)

# Count total models
TOTAL_MODELS=0
for category in "${!MODEL_STACK[@]}"; do
    models=(${MODEL_STACK[$category]})
    TOTAL_MODELS=$((TOTAL_MODELS + ${#models[@]}))
done

echo -e "${CYAN}🎯 Starting download of $TOTAL_MODELS models...${NC}"

# Results tracking
RESULTS_FILE="$OUTPUT_PATH/download_results_$(date +%Y%m%d_%H%M%S).json"
echo "[]" > "$RESULTS_FILE"

# Download function
download_model() {
    local model_name="$1"
    local category="$2"
    
    echo -e "${YELLOW}⬇️  Downloading $category: $model_name${NC}"
    
    if ollama pull "$model_name" 2>/dev/null; then
        echo -e "${GREEN}✅ Successfully downloaded: $model_name${NC}"
        echo "{\"model\": \"$model_name\", \"status\": \"Success\", \"category\": \"$category\"}" >> "$RESULTS_FILE.tmp"
        return 0
    else
        echo -e "${RED}❌ Failed to download: $model_name${NC}"
        echo "{\"model\": \"$model_name\", \"status\": \"Failed\", \"category\": \"$category\"}" >> "$RESULTS_FILE.tmp"
        return 1
    fi
}

# Initialize results temp file
echo "" > "$RESULTS_FILE.tmp"

if [ "$PARALLEL" = true ]; then
    echo -e "${BLUE}🔄 Using parallel downloads (max $MAX_CONCURRENT concurrent)${NC}"
    
    # Create job queue
    JOB_QUEUE=()
    for category in "${!MODEL_STACK[@]}"; do
        models=(${MODEL_STACK[$category]})
        for model in "${models[@]}"; do
            JOB_QUEUE+=("$model|$category")
        done
    done
    
    # Process jobs with limited concurrency
    ACTIVE_JOBS=0
    JOB_INDEX=0
    
    while [ $JOB_INDEX -lt ${#JOB_QUEUE[@]} ] || [ $ACTIVE_JOBS -gt 0 ]; do
        # Start new jobs if under limit and jobs available
        while [ $ACTIVE_JOBS -lt $MAX_CONCURRENT ] && [ $JOB_INDEX -lt ${#JOB_QUEUE[@]} ]; do
            IFS='|' read -r model category <<< "${JOB_QUEUE[$JOB_INDEX]}"
            download_model "$model" "$category" &
            ((ACTIVE_JOBS++))
            ((JOB_INDEX++))
        done
        
        # Wait for any job to complete
        if [ $ACTIVE_JOBS -gt 0 ]; then
            wait -n
            ((ACTIVE_JOBS--))
        fi
    done
    
else
    # Sequential downloads
    CURRENT=0
    for category in "${!MODEL_STACK[@]}"; do
        echo -e "\n${MAGENTA}📦 Downloading $category models...${NC}"
        
        models=(${MODEL_STACK[$category]})
        for model in "${models[@]}"; do
            ((CURRENT++))
            echo -e "${BLUE}Progress: $CURRENT/$TOTAL_MODELS${NC}"
            download_model "$model" "$category"
        done
    done
fi

# Process results
echo -e "\n${CYAN}📊 Download Summary Report${NC}"
echo -e "${CYAN}=========================${NC}"

# Count successes and failures
SUCCESSFUL=$(grep -c '"status": "Success"' "$RESULTS_FILE.tmp" || echo "0")
FAILED=$(grep -c '"status": "Failed"' "$RESULTS_FILE.tmp" || echo "0")

echo -e "${GREEN}✅ Successful downloads: $SUCCESSFUL${NC}"
echo -e "${RED}❌ Failed downloads: $FAILED${NC}"

if [ $TOTAL_MODELS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $SUCCESSFUL * 100 / $TOTAL_MODELS" | bc -l)
    echo -e "${BLUE}📈 Success rate: ${SUCCESS_RATE}%${NC}"
fi

# Create proper JSON array
echo "[" > "$RESULTS_FILE"
sed 's/$/,/' "$RESULTS_FILE.tmp" | sed '$s/,$//' >> "$RESULTS_FILE"
echo "]" >> "$RESULTS_FILE"
rm "$RESULTS_FILE.tmp"

echo -e "\n${GREEN}📄 Detailed report saved to: $RESULTS_FILE${NC}"

# Verify installations if not skipped
if [ "$SKIP_VALIDATION" = false ]; then
    echo -e "\n${YELLOW}🔍 Verifying model installations...${NC}"
    
    INSTALLED_MODELS=$(ollama list | tail -n +2 | awk '{print $1}')
    
    while IFS= read -r line; do
        if [[ $line == *'"status": "Success"'* ]]; then
            model=$(echo "$line" | grep -o '"model": "[^"]*"' | cut -d'"' -f4)
            if echo "$INSTALLED_MODELS" | grep -q "$model"; then
                echo -e "${GREEN}✅ Verified: $model${NC}"
            else
                echo -e "${YELLOW}⚠️  Not found in list: $model${NC}"
            fi
        fi
    done < <(grep '"status": "Success"' "$RESULTS_FILE")
fi

# Display failed downloads
if [ $FAILED -gt 0 ]; then
    echo -e "\n${RED}❌ Failed Downloads:${NC}"
    while IFS= read -r line; do
        if [[ $line == *'"status": "Failed"'* ]]; then
            model=$(echo "$line" | grep -o '"model": "[^"]*"' | cut -d'"' -f4)
            category=$(echo "$line" | grep -o '"category": "[^"]*"' | cut -d'"' -f4)
            echo -e "  ${RED}- $model ($category)${NC}"
        fi
    done < <(grep '"status": "Failed"' "$RESULTS_FILE")
fi

# Phoenix Hydra integration commands
# Initialize Phoenix Model Manager if available
if [ "$PYTHON_MANAGER_AVAILABLE" = true ]; then
    echo -e "\n${CYAN}🔧 Initializing Phoenix Model Manager...${NC}"
    python3 -c "
from src.core.model_manager import model_manager
import asyncio

async def initialize_models():
    print('📊 Loading model configurations...')
    model_manager.load_config()
    
    print('🔍 Checking model status...')
    models = model_manager.list_models()
    downloaded = len([m for m in models if m['status'] == 'downloaded'])
    total = len(models)
    
    print(f'✅ Model Manager initialized: {downloaded}/{total} models ready')
    
    # Save updated configuration
    model_manager._save_config()
    print('💾 Configuration saved')

asyncio.run(initialize_models())
"
fi

echo -e "\n${CYAN}🔧 Phoenix Hydra Integration Commands:${NC}"
echo -e "${CYAN}=====================================${NC}"
echo -e "${NC}# Start Phoenix Hydra with 2025 models:${NC}"
echo -e "${NC}podman-compose -f infra/podman/podman-compose.yaml up -d${NC}"
echo -e "\n${NC}# Start Model Service:${NC}"
echo -e "${NC}python -m src.services.model_service${NC}"
echo -e "\n${NC}# Test model inference via API:${NC}"
echo -e "${NC}curl -X POST http://localhost:8090/inference -H 'Content-Type: application/json' -d '{\"model_type\": \"reasoning\", \"prompt\": \"Hello Phoenix Hydra!\"}'${NC}"
echo -e "\n${NC}# Load all downloaded models:${NC}"
echo -e "${NC}curl -X POST http://localhost:8090/models/download${NC}"
echo -e "\n${NC}# Check system health:${NC}"
echo -e "${NC}curl http://localhost:8090/health${NC}"
echo -e "\n${NC}# List available models:${NC}"
echo -e "${NC}curl http://localhost:8090/models${NC}"

echo -e "\n${GREEN}🎉 Phoenix Hydra 2025 Model Stack download complete!${NC}"
echo -e "${CYAN}Ready for 100% local AI processing with energy-efficient SSM architecture!${NC}"
echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "${NC}1. Start the model service: python -m src.services.model_service${NC}"
echo -e "${NC}2. Load models via API or web interface${NC}"
echo -e "${NC}3. Deploy Phoenix Hydra stack: ./deploy.sh${NC}"
echo -e "${NC}4. Access model management at: http://localhost:8090${NC}"