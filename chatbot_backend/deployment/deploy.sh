#!/bin/bash

# =============================================================================
# ENTERPRISE-GRADE CLOUD RUN BUILDPACK DEPLOYMENT SCRIPT
# =============================================================================
# Version: 2.0
# Author: AI Agent Service Team
# Description: Enhanced deployment script with comprehensive validation,
#              error handling, and enterprise-grade safety checks
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# CONFIGURATION & DEFAULTS
# =============================================================================

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
readonly LOG_FILE="$PROJECT_ROOT/deployment_$TIMESTAMP.log"

# Default configuration
PROJECT_ID=${1:-"ai-chatbot-472322"}
REGION=${2:-"us-central1"}
SERVICE_NAME=${3:-"ai-agent-service"}
DEPLOY_MODE=${4:-"traffic"}  # traffic|no-traffic
TIMEOUT=${5:-"900"}

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "${BLUE}ℹ️  $*${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}✅ $*${NC}"
}

log_warning() {
    log "WARNING" "${YELLOW}⚠️  $*${NC}"
}

log_error() {
    log "ERROR" "${RED}❌ $*${NC}"
}

log_step() {
    log "STEP" "${PURPLE}🔄 $*${NC}"
}

log_debug() {
    if [[ "${DEBUG_MODE:-false}" == "true" ]]; then
        log "DEBUG" "${CYAN}🔍 $*${NC}"
    fi
}

# =============================================================================
# ERROR HANDLING
# =============================================================================

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code: $exit_code"
        log_error "Check log file: $LOG_FILE"
        log_info "Troubleshooting steps:"
        log_info "1. Verify gcloud authentication: gcloud auth list"
        log_info "2. Check project permissions: gcloud projects get-iam-policy $PROJECT_ID"
        log_info "3. Validate buildpack files: runtime.txt, Procfile, requirements.txt"
        log_info "4. Review Cloud Run service logs: gcloud logging read"
    fi
}

trap cleanup EXIT

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_numeric() {
    [[ $1 =~ ^[0-9]+$ ]]
}

validate_project_id() {
    local project_id="$1"
    if [[ ! "$project_id" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]]; then
        log_error "Invalid project ID format: $project_id"
        log_info "Project ID must be 6-30 characters, start with lowercase letter, contain only lowercase letters, numbers, and hyphens"
        return 1
    fi
}

validate_region() {
    local region="$1"
    local valid_regions=("us-central1" "us-east1" "us-west1" "europe-west1" "asia-east1" "asia-northeast1")
    for valid_region in "${valid_regions[@]}"; do
        if [[ "$region" == "$valid_region" ]]; then
            return 0
        fi
    done
    log_error "Invalid region: $region"
    log_info "Valid regions: ${valid_regions[*]}"
    return 1
}

# =============================================================================
# DEPENDENCY VALIDATION
# =============================================================================

validate_dependencies() {
    log_step "Validating system dependencies..."

    local missing_deps=()

    # Check required commands
    local required_commands=("gcloud" "curl" "grep" "awk")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies and try again"
        return 1
    fi

    log_success "All system dependencies found"
    return 0
}

# =============================================================================
# GCLOUD AUTHENTICATION VALIDATION
# =============================================================================

validate_gcloud_auth() {
    log_step "Validating gcloud authentication..."

    # Check if authenticated
    if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -n1 | grep -q '@'; then
        log_error "No active gcloud authentication found"
        log_info "Run: gcloud auth login"
        return 1
    fi

    local active_account
    active_account=$(gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -n1)
    log_success "Authenticated as: $active_account"

    # Validate project access
    if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
        log_error "Cannot access project: $PROJECT_ID"
        log_info "Check project ID and permissions"
        return 1
    fi

    log_success "Project access validated: $PROJECT_ID"

    # Check Cloud Run API
    if ! gcloud services list --enabled --filter="name:run.googleapis.com" --format="value(name)" | grep -q "run.googleapis.com"; then
        log_warning "Cloud Run API may not be enabled"
        log_info "Enabling Cloud Run API..."
        if ! gcloud services enable run.googleapis.com --project="$PROJECT_ID"; then
            log_error "Failed to enable Cloud Run API"
            return 1
        fi
        log_success "Cloud Run API enabled"
    fi

    return 0
}

# =============================================================================
# BUILDPACK CONFIGURATION VALIDATION
# =============================================================================

validate_buildpack_config() {
    log_step "Validating buildpack configuration..."

    local config_errors=()

    # Check .python-version
    if [[ -f ".python-version" ]]; then
        local python_version
        python_version=$(cat .python-version | tr -d '\r\n')
        if [[ ! "$python_version" =~ ^3\.(8|9|10|11|12)$ ]]; then
            config_errors+=(".python-version contains unsupported version: $python_version (supported: 3.8-3.12)")
        else
            log_success ".python-version: $python_version"
        fi
    else
        config_errors+=(".python-version file missing")
    fi

    # Check runtime.txt
    if [[ -f "runtime.txt" ]]; then
        local runtime
        runtime=$(cat runtime.txt | tr -d '\r\n')
        if [[ ! "$runtime" =~ ^python-3\.(8|9|10|11|12)$ ]]; then
            config_errors+=("runtime.txt contains invalid format: $runtime (expected: python-3.x)")
        else
            log_success "runtime.txt: $runtime"
        fi
    else
        config_errors+=("runtime.txt file missing")
    fi

    # Check Procfile
    if [[ -f "Procfile" ]]; then
        if ! grep -q "web:" Procfile; then
            config_errors+=("Procfile missing 'web:' process type")
        else
            local web_command
            web_command=$(grep "^web:" Procfile | cut -d: -f2- | xargs)
            log_success "Procfile web command: $web_command"
        fi
    else
        config_errors+=("Procfile missing")
    fi

    # Check requirements.txt
    if [[ -f "requirements.txt" ]]; then
        # Validate key dependencies
        local required_packages=("fastapi" "uvicorn" "google-cloud-aiplatform")
        for package in "${required_packages[@]}"; do
            if ! grep -q "^$package" requirements.txt; then
                config_errors+=("requirements.txt missing required package: $package")
            fi
        done

        local package_count
        package_count=$(grep -c "^[a-zA-Z]" requirements.txt)
        log_success "requirements.txt: $package_count packages found"
    else
        config_errors+=("requirements.txt missing")
    fi

    # Check main.py entry point
    if [[ ! -f "main.py" ]]; then
        config_errors+=("main.py entry point missing")
    else
        if ! grep -q "uvicorn\|fastapi\|app" main.py; then
            config_errors+=("main.py doesn't appear to be a valid FastAPI entry point")
        else
            log_success "main.py entry point validated"
        fi
    fi

    if [[ ${#config_errors[@]} -gt 0 ]]; then
        log_error "Buildpack configuration issues found:"
        for error in "${config_errors[@]}"; do
            log_error "  - $error"
        done
        return 1
    fi

    log_success "Buildpack configuration validated"
    return 0
}

# =============================================================================
# PROJECT STRUCTURE VALIDATION
# =============================================================================

validate_project_structure() {
    log_step "Validating project structure..."

    local structure_errors=()

    # Check required directories
    local required_dirs=("app" "api" "agent" "app/vector-files")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            structure_errors+=("Required directory missing: $dir")
        else
            log_debug "Directory found: $dir"
        fi
    done

    # Check vector files
    if [[ -d "app/vector-files" ]]; then
        local vector_files
        vector_files=$(find app/vector-files -name "*.npy" -o -name "*.pkl" -o -name "*.index" 2>/dev/null | wc -l)
        if [[ $vector_files -eq 0 ]]; then
            structure_errors+=("No vector files found in app/vector-files")
        else
            log_success "Vector files found: $vector_files files"
        fi
    fi

    # Check environment configuration
    if [[ -f ".env.example" ]] && [[ ! -f ".env" ]]; then
        log_warning ".env file not found, using environment variables"
        log_info "Consider creating .env from .env.example for local development"
    fi

    if [[ ${#structure_errors[@]} -gt 0 ]]; then
        log_error "Project structure issues found:"
        for error in "${structure_errors[@]}"; do
            log_error "  - $error"
        done
        return 1
    fi

    log_success "Project structure validated"
    return 0
}

# =============================================================================
# ENVIRONMENT VARIABLES PREPARATION
# =============================================================================

prepare_environment_variables() {
    log_step "Preparing environment variables..."

    # Load .env if it exists
    if [[ -f ".env" ]]; then
        log_info "Loading environment from .env file"
        # shellcheck source=/dev/null
        source .env || log_warning "Failed to source .env file"
    fi

    # Create temporary env file for reliable deployment
    local temp_env_file="temp-env-vars-$TIMESTAMP.txt"

    {
        echo "PROJECT_ID=$PROJECT_ID"
        echo "LOCATION=$REGION"
        echo "IS_LOCAL=false"
        echo "LOCAL_VECTOR_FILES_PATH=app/vector-files"
        echo "DEPLOYMENT_TIMESTAMP=$TIMESTAMP"

        # Add optional environment variables if they exist
        [[ -n "${DEBUG_MODE:-}" ]] && echo "DEBUG_MODE=$DEBUG_MODE"
        [[ -n "${CORS_ORIGINS:-}" ]] && echo "CORS_ORIGINS=$CORS_ORIGINS"
        [[ -n "${GENERATIVE_MODEL_NAME:-}" ]] && echo "GENERATIVE_MODEL_NAME=$GENERATIVE_MODEL_NAME"
        [[ -n "${EMBEDDING_MODEL_NAME:-}" ]] && echo "EMBEDDING_MODEL_NAME=$EMBEDDING_MODEL_NAME"
        [[ -n "${DEFAULT_VOICE_NAME:-}" ]] && echo "DEFAULT_VOICE_NAME=$DEFAULT_VOICE_NAME"
        [[ -n "${FIREBASE_PROJECT_ID:-}" ]] && echo "FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID"
        [[ -n "${FIREBASE_STORAGE_BUCKET:-}" ]] && echo "FIREBASE_STORAGE_BUCKET=$FIREBASE_STORAGE_BUCKET"
    } > "$temp_env_file"

    log_info "Created environment file: $temp_env_file"
    log_debug "Environment variables written to file for safe deployment"

    echo "$temp_env_file"
}

# =============================================================================
# CLOUD RUN DEPLOYMENT
# =============================================================================

deploy_service() {
    log_step "Deploying to Cloud Run..."

    local env_file
    env_file=$(prepare_environment_variables)

    # Ensure cleanup of temp file
    trap "rm -f '$env_file'" EXIT

    local deploy_args=(
        "run" "deploy" "$SERVICE_NAME"
        "--source" "."
        "--region" "$REGION"
        "--allow-unauthenticated"
        "--env-vars-file" "$env_file"
        "--memory" "4Gi"
        "--cpu" "2"
        "--max-instances" "10"
        "--timeout" "$TIMEOUT"
        "--platform" "managed"
        "--project" "$PROJECT_ID"
    )

    # Add traffic management
    if [[ "$DEPLOY_MODE" == "no-traffic" ]]; then
        deploy_args+=("--no-traffic")
        log_info "Deploying with --no-traffic flag (safer deployment)"
    fi

    # Add service account if specified
    if [[ -n "${SERVICE_ACCOUNT:-}" ]]; then
        deploy_args+=("--service-account" "$SERVICE_ACCOUNT")
        log_info "Using service account: $SERVICE_ACCOUNT"
    fi

    log_info "Deploying with environment file: $env_file"
    log_info "Executing: gcloud ${deploy_args[*]}"

    if ! gcloud "${deploy_args[@]}"; then
        log_error "Cloud Run deployment failed"
        log_info "Common solutions:"
        log_info "1. Check quotas: gcloud compute project-info describe --project=$PROJECT_ID"
        log_info "2. Verify IAM permissions for Cloud Run"
        log_info "3. Check build logs in Cloud Console"
        log_info "4. Check environment file: $env_file"
        return 1
    fi

    # Clean up temp file
    rm -f "$env_file"

    log_success "Service deployed successfully!"
    return 0
}

# =============================================================================
# HEALTH CHECKING
# =============================================================================

wait_for_service() {
    local service_url="$1"
    local max_attempts=30
    local wait_interval=10

    log_step "Waiting for service to become ready..."

    for ((i=1; i<=max_attempts; i++)); do
        log_info "Health check attempt $i/$max_attempts..."

        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$service_url/health" 2>/dev/null || echo "000")

        case "$http_code" in
            200)
                log_success "Service is healthy (HTTP $http_code)"
                return 0
                ;;
            000)
                log_warning "Connection failed (attempt $i/$max_attempts)"
                ;;
            *)
                log_warning "Service returned HTTP $http_code (attempt $i/$max_attempts)"
                ;;
        esac

        if [[ $i -lt $max_attempts ]]; then
            log_info "Waiting ${wait_interval}s before next attempt..."
            sleep $wait_interval
        fi
    done

    log_error "Service failed to become ready after $max_attempts attempts"
    return 1
}

comprehensive_health_check() {
    local service_url="$1"

    log_step "Performing comprehensive health check..."

    # Test health endpoint
    if ! wait_for_service "$service_url"; then
        log_error "Basic health check failed"
        return 1
    fi

    # Test additional endpoints
    local endpoints=("/health" "/debug/faiss-status")

    for endpoint in "${endpoints[@]}"; do
        log_info "Testing endpoint: $endpoint"
        local response
        response=$(curl -s --connect-timeout 10 --max-time 30 "$service_url$endpoint" 2>/dev/null || echo "ERROR")

        if [[ "$response" == "ERROR" ]]; then
            log_warning "Endpoint $endpoint failed"
        else
            log_success "Endpoint $endpoint responded"
            log_debug "Response: ${response:0:100}..."
        fi
    done

    return 0
}

# =============================================================================
# DEPLOYMENT SUMMARY
# =============================================================================

print_deployment_summary() {
    local service_url="$1"

    log_success "=== DEPLOYMENT COMPLETED SUCCESSFULLY ==="
    log_info "Service: $SERVICE_NAME"
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "URL: $service_url"
    log_info "Timestamp: $TIMESTAMP"
    log_info "Log file: $LOG_FILE"

    if [[ "$DEPLOY_MODE" == "no-traffic" ]]; then
        log_info ""
        log_warning "⚠️  Deployed with --no-traffic flag"
        log_info "To route traffic to the new revision:"
        log_info "gcloud run services update-traffic $SERVICE_NAME --to-latest --region=$REGION --project=$PROJECT_ID"
    fi

    log_info ""
    log_info "🧪 Test endpoints:"
    log_info "Health: curl $service_url/health"
    log_info "FAISS Status: curl $service_url/debug/faiss-status"
    log_info "Chat: curl -X POST $service_url/chat/send -H 'Content-Type: application/json' -d '{\"message\":\"test\"}'"

    log_info ""
    log_info "📊 Monitor deployment:"
    log_info "Logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME' --limit=50 --project=$PROJECT_ID"
    log_info "Metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    log_info "=== ENTERPRISE-GRADE CLOUD RUN BUILDPACK DEPLOYMENT ==="
    log_info "Script: $SCRIPT_NAME"
    log_info "Version: 2.0"
    log_info "Timestamp: $TIMESTAMP"
    log_info "Working directory: $PROJECT_ROOT"
    log_info ""

    # Input validation
    validate_project_id "$PROJECT_ID" || exit 1
    validate_region "$REGION" || exit 1

    if ! is_numeric "$TIMEOUT" || [[ $TIMEOUT -lt 60 ]] || [[ $TIMEOUT -gt 3600 ]]; then
        log_error "Invalid timeout: $TIMEOUT (must be 60-3600 seconds)"
        exit 1
    fi

    log_info "Configuration:"
    log_info "  Project ID: $PROJECT_ID"
    log_info "  Region: $REGION"
    log_info "  Service: $SERVICE_NAME"
    log_info "  Deploy Mode: $DEPLOY_MODE"
    log_info "  Timeout: ${TIMEOUT}s"
    log_info ""

    # Change to project root
    cd "$PROJECT_ROOT" || {
        log_error "Failed to change to project root: $PROJECT_ROOT"
        exit 1
    }

    # Run all validations
    validate_dependencies || exit 1
    validate_gcloud_auth || exit 1
    validate_buildpack_config || exit 1
    validate_project_structure || exit 1

    # Deploy the service
    if ! deploy_service; then
        log_error "Deployment failed"
        exit 1
    fi

    # Get service URL
    log_step "Retrieving service URL..."
    local service_url
    service_url=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format "value(status.url)" --project "$PROJECT_ID" 2>/dev/null)

    if [[ -z "$service_url" ]]; then
        log_error "Failed to retrieve service URL"
        exit 1
    fi

    log_success "Service URL: $service_url"

    # Comprehensive health checking
    if [[ "$DEPLOY_MODE" == "traffic" ]]; then
        comprehensive_health_check "$service_url" || {
            log_warning "Health checks failed, but deployment completed"
            log_info "Service may need additional time to initialize"
        }
    else
        log_info "Skipping health checks (no-traffic deployment)"
    fi

    # Print deployment summary
    print_deployment_summary "$service_url"

    log_success "🎉 Deployment completed successfully!"
}

# Run main function
main "$@"