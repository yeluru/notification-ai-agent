# GitHub Setup Instructions

## Quick Setup

### 1. Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `notification-agent` (or your preferred name)
3. Description: "Multi-source notification agent with email, LinkedIn, Twitter support"
4. Choose Public or Private
5. **Don't** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### 2. Add Remote and Push

#### Option A: HTTPS (easier, requires GitHub login)
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

#### Option B: SSH (requires SSH key setup)
```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 3. Verify
- Visit your GitHub repository
- Check that all files are there
- Verify `.env` and `*.db` files are **NOT** visible (they're in .gitignore)

## Future Updates

After making changes:
```bash
git add .
git commit -m "Your commit message"
git push
```

## Troubleshooting

**If you get "remote origin already exists":**
```bash
git remote remove origin
git remote add origin YOUR_REPO_URL
```

**If you need to change the branch name:**
```bash
git branch -M main  # Rename current branch to main
```

**If push is rejected:**
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```
