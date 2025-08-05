#!/bin/bash
# Phoenix Hydra 2025 Advanced AI Model Stack Downloader
# Automated download script for the complete 2025 model ecosystem

set -euo pipefail

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

# 2025 Advanced Model Ecosystem
declare -A MODEL_STACK=(
    ["Core SSM/Mamba Models"]="mamba-7b mamba-13b mamba-30b state-spaces/mamba-130m state-spaces/mamba-370m state-spaces/mamba-790m"
    ["2025 Flagship Models"]="minimax/abab6.5s-chat minimax/abab6.5g-chat kimi/moonshot-v1-8k kimi/moonshot-v1-32k kimi/moonshot-v1-128k flux/kontext-7b flux/kontext-13b glm-4.5-chat glm-4.5-coder qwen2.5-coder:7b qwen2.5-coder:14b qwen2.5-coder:32b"
    ["Specialized Coding Models"]="deepseek-coder-v2:16b deepseek-coder-v2:236b codestral:22b codegemma:7b starcoder2:7b starcoder2:15b"
    ["Local Processing Optimized"]="phi3:mini phi3:medium gemma2:2b gemma2:9b llama3.2:1b llama3.2:3b mistral-nemo:12b"
    ["Biomimetic Agent Models"]="neural-chat:7b orca-mini:3b orca-mini:7b vicuna:7b vicuna:13b"
    ["Energy Efficient Models"]="tinyllama:1.1b stablelm2:1.6b stablelm2:12b openchat:7b solar:10.7b"
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
echo -e "\n${CYAN}🔧 Phoenix Hydra Integration Commands:${NC}"
echo -e "${CYAN}=====================================${NC}"
echo -e "${NC}# Start Phoenix Hydra with 2025 models:${NC}"
echo -e "${NC}podman-compose -f infra/podman/compose.yaml up -d${NC}"
echo -e "\n${NC}# Test local processing pipeline:${NC}"
echo -e "${NC}python examples/local_processing_demo.py${NC}"
echo -e "\n${NC}# Run RUBIK biomimetic agents:${NC}"
echo -e "${NC}python examples/rubik_ecosystem_demo.py${NC}"
echo -e "\n${NC}# Test SSM analysis engines:${NC}"
echo -e "${NC}python examples/ssm_analysis_demo.py${NC}"

echo -e "\n${GREEN}🎉 Phoenix Hydra 2025 Model Stack download complete!${NC}"
echo -e "${CYAN}Ready for 100% local AI processing with energy-efficient SSM architecture!${NC}"