#!/bin/bash

# Terraform wrapper script for ACE Fitness infrastructure
set -e

# Configuration
TF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TFVARS_FILE="$TF_DIR/terraform.tfvars"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform first."
        echo "Visit: https://learn.hashicorp.com/tutorials/terraform/install-cli"
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install Google Cloud CLI first."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Please run: gcloud auth login"
        exit 1
    fi
    
    print_status "All prerequisites are met"
}

# Setup terraform vars file
setup_tfvars() {
    if [ ! -f "$TFVARS_FILE" ]; then
        print_status "Creating terraform.tfvars from example..."
        cp "$TF_DIR/terraform.tfvars.example" "$TFVARS_FILE"
        print_warning "Please review and customize $TFVARS_FILE if needed"
    fi
}

# Initialize Terraform
terraform_init() {
    print_section "Initializing Terraform"
    cd "$TF_DIR"
    
    terraform init
    
    print_status "Terraform initialized successfully"
}

# Plan infrastructure changes
terraform_plan() {
    print_section "Planning Infrastructure Changes"
    cd "$TF_DIR"
    
    terraform plan -var-file="$TFVARS_FILE" -out=tfplan
    
    print_status "Terraform plan completed. Review the changes above."
}

# Apply infrastructure changes
terraform_apply() {
    print_section "Applying Infrastructure Changes"
    cd "$TF_DIR"
    
    if [ -f "tfplan" ]; then
        terraform apply tfplan
        rm -f tfplan
    else
        terraform apply -var-file="$TFVARS_FILE" -auto-approve
    fi
    
    print_status "Infrastructure deployment completed!"
    print_section "📋 Deployment Summary"
    terraform output
}

# Destroy infrastructure
terraform_destroy() {
    print_section "⚠️  DESTROY INFRASTRUCTURE ⚠️"
    print_warning "This will PERMANENTLY DELETE all infrastructure!"
    echo ""
    terraform output 2>/dev/null || echo "No existing infrastructure found"
    echo ""
    
    read -p "Are you absolutely sure you want to destroy everything? (type 'DESTROY' to confirm): " confirmation
    
    if [ "$confirmation" != "DESTROY" ]; then
        echo "Destruction cancelled. No resources were deleted."
        exit 0
    fi
    
    cd "$TF_DIR"
    terraform destroy -var-file="$TFVARS_FILE" -auto-approve
    
    print_status "Infrastructure destroyed successfully"
}

# Show current state
terraform_show() {
    print_section "Current Infrastructure State"
    cd "$TF_DIR"
    
    if terraform show | grep -q "No state"; then
        print_warning "No infrastructure found"
    else
        echo "📊 Resource Summary:"
        terraform output 2>/dev/null || echo "No outputs available"
        echo ""
        echo "💰 Estimated Monthly Cost:"
        echo "  • GKE Cluster (3 nodes): ~\$72"
        echo "  • LoadBalancers (2): ~\$36"
        echo "  • Static IPs (2): ~\$6"
        echo "  • Artifact Registry: ~\$1"
        echo "  📊 Total: ~\$115/month"
    fi
}

# Get kubectl access
configure_kubectl() {
    print_section "Configuring kubectl Access"
    cd "$TF_DIR"
    
    # Get the kubectl command from terraform output
    KUBECTL_CMD=$(terraform output -raw kubectl_command 2>/dev/null)
    
    if [ -z "$KUBECTL_CMD" ]; then
        print_error "No cluster found. Please deploy infrastructure first."
        exit 1
    fi
    
    print_status "Running: $KUBECTL_CMD"
    eval "$KUBECTL_CMD"
    
    print_status "kubectl configured successfully!"
    echo "Test with: kubectl get nodes"
}

# Show access information
show_access_info() {
    print_section "Access Information"
    cd "$TF_DIR"
    
    JENKINS_URL=$(terraform output -raw jenkins_url 2>/dev/null)
    APP_URL=$(terraform output -raw app_url 2>/dev/null)
    ADMIN_CMD=$(terraform output -raw jenkins_admin_password_command 2>/dev/null)
    
    if [ ! -z "$JENKINS_URL" ]; then
        print_status "🚀 Your Services:"
        echo "  Jenkins: $JENKINS_URL"
        echo "  Application: $APP_URL (after deployment)"
        echo ""
        print_status "🔐 Get Jenkins Admin Password:"
        echo "  $ADMIN_CMD"
        echo ""
        print_status "🎯 Next Steps:"
        echo "  1. Access Jenkins at the URL above"
        echo "  2. Configure Jenkins with required plugins"
        echo "  3. Create pipeline job pointing to your Jenkinsfile"
        echo "  4. Run pipeline to deploy your application"
    else
        print_error "No infrastructure found. Please deploy first with: $0 apply"
    fi
}

# Main help function
show_help() {
    echo "ACE Fitness Infrastructure Management (Terraform)"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  init     - Initialize Terraform (required first step)"
    echo "  plan     - Show planned infrastructure changes"
    echo "  apply    - Deploy infrastructure"
    echo "  destroy  - Destroy all infrastructure"
    echo "  show     - Show current infrastructure state"
    echo "  kubectl  - Configure kubectl for cluster access"
    echo "  access   - Show access URLs and commands"
    echo "  help     - Show this help message"
    echo ""
    echo "Typical workflow:"
    echo "  1. $0 init     # Initialize Terraform"
    echo "  2. $0 plan     # Review changes"
    echo "  3. $0 apply    # Deploy infrastructure"
    echo "  4. $0 kubectl  # Configure kubectl"
    echo "  5. $0 access   # Get access information"
    echo ""
    echo "Cleanup:"
    echo "  $0 destroy     # Remove all infrastructure"
}

# Main execution
main() {
    case "${1:-help}" in
        "init")
            check_prerequisites
            setup_tfvars
            terraform_init
            ;;
        "plan")
            check_prerequisites
            terraform_plan
            ;;
        "apply")
            check_prerequisites
            setup_tfvars
            terraform_init
            terraform_plan
            terraform_apply
            configure_kubectl
            show_access_info
            ;;
        "destroy")
            check_prerequisites
            terraform_destroy
            ;;
        "show")
            terraform_show
            ;;
        "kubectl")
            configure_kubectl
            ;;
        "access")
            show_access_info
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"