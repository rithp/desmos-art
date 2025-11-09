#!/bin/bash

# Quick Deployment Script for Desmos Art Converter
# This script helps you prepare and deploy your app

echo "🚀 Desmos Art Converter - Deployment Helper"
echo "==========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not found. Please initialize git first."
    exit 1
fi

echo "📋 Pre-deployment Checklist:"
echo ""

# Check for required files
echo "Checking required files..."

files=("app.py" "base.py" "requirements-production.txt" "Procfile" "render.yaml" "templates/index.html" "static/style.css")
all_files_exist=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING!"
        all_files_exist=false
    fi
done

echo ""

if [ "$all_files_exist" = false ]; then
    echo "❌ Some required files are missing. Please fix before deploying."
    exit 1
fi

# Check git status
echo "📊 Git Status:"
git status --short
echo ""

# Ask user what to do
echo "What would you like to do?"
echo "1) Commit and push changes to GitHub"
echo "2) Just show deployment instructions"
echo "3) Exit"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        read -p "Enter commit message: " commit_msg
        
        if [ -z "$commit_msg" ]; then
            commit_msg="Update for deployment"
        fi
        
        git add .
        git commit -m "$commit_msg"
        git push
        
        echo ""
        echo "✅ Changes pushed to GitHub!"
        echo ""
        echo "📝 Next Steps for Render Deployment:"
        echo "1. Go to https://render.com and sign up/login"
        echo "2. Click 'New +' → 'Web Service'"
        echo "3. Connect your GitHub repository: desmos-art"
        echo "4. Render will auto-detect the render.yaml configuration"
        echo "5. Click 'Create Web Service'"
        echo "6. Wait 5-10 minutes for deployment"
        echo "7. Your app will be live! 🎉"
        echo ""
        ;;
    2)
        echo ""
        echo "📝 Deployment Instructions:"
        echo ""
        echo "OPTION 1 - Render (Recommended):"
        echo "1. Push your code to GitHub (if not done)"
        echo "2. Go to https://render.com"
        echo "3. Sign up/login with GitHub"
        echo "4. Click 'New +' → 'Web Service'"
        echo "5. Select your 'desmos-art' repository"
        echo "6. Render will use the render.yaml config automatically"
        echo "7. Click 'Create Web Service'"
        echo "8. Wait for deployment to complete"
        echo ""
        echo "OPTION 2 - Railway:"
        echo "1. Go to https://railway.app"
        echo "2. Click 'Deploy from GitHub repo'"
        echo "3. Select your repository"
        echo "4. Railway auto-detects Python and uses Procfile"
        echo "5. Click 'Deploy'"
        echo ""
        echo "OPTION 3 - Fly.io:"
        echo "1. Install Fly CLI: curl -L https://fly.io/install.sh | sh"
        echo "2. Run: fly auth signup (or fly auth login)"
        echo "3. Run: fly launch"
        echo "4. Run: fly deploy"
        echo ""
        echo "For detailed instructions, see DEPLOYMENT_GUIDE.md"
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "🎉 Good luck with your deployment!"
