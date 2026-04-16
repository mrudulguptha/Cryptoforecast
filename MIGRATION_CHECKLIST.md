# 🔄 MIGRATION CHECKLIST - Replace Old Files

## Step 1: Backup Originals (Safety First!)

```powershell
# Navigate to project
cd "c:\VS CODE\CryptoForecast"

# Backup folder
mkdir backup
cp app.py backup/app.py
cp check.py backup/check.py
cp daily.py backup/daily.py
cp hourly.py backup/hourly.py
cp train_models.py backup/train_models.py
```

## Step 2: Replace with Refactored Versions

```powershell
# Remove old files
rm app.py
rm check.py
rm daily.py
rm hourly.py
rm train_models.py

# Rename new files to replace
mv app_new.py app.py
mv check_new.py check.py
mv daily_new.py daily.py
mv hourly_new.py hourly.py
mv train_models_new.py train_models.py
```

## Step 3: Verify Installation

```powershell
# Check files exist
ls app.py, check.py, daily.py, hourly.py, train_models.py

# Verify imports work
python -c "import app; print('✅ app.py OK')"
python -c "import check; print('✅ check.py OK')"
```

## Step 4: Test Locally

```powershell
# Install requirements (if not done)
pip install -r requirements.txt

# Set environment variables (Windows PowerShell)
$env:FLASK_ENV = "development"
$env:PORT = "5000"

# Or create .env file and use python-dotenv
# For now, just run:
python app.py

# Open browser: http://localhost:5000
# Test prediction endpoint
# Press CTRL+C to stop
```

## Step 5: Prepare Git

```powershell
# Check git status
git status

# Add new files
git add requirements.txt Procfile .gitignore .env.example DEPLOYMENT.md REFACTORING_SUMMARY.md

# Add modified Python files
git add app.py check.py daily.py hourly.py train_models.py

# Commit
git commit -m "refactor: Optimize for Render deployment

- Use dynamic PORT from environment
- Fix all file paths to be relative
- Move API keys to environment variables
- Implement lazy loading for FinBERT
- Add model caching layer
- Improve error handling across all modules
- Add requirements.txt for pip installation
- Create Procfile for Gunicorn/Render
- Add comprehensive deployment documentation"

# Remove old files from git (optional)
git rm --cached app_new.py check_new.py daily_new.py hourly_new.py train_models_new.py
git commit -m "clean: Remove temporary refactored file copies"
```

## Step 6: Deploy to Render

```powershell
# Push to GitHub
git push origin main

# OR if using Render CLI:
# npm install -g @render-com/cli
# render deploy
```

---

## ✅ Verification Checklist

- [ ] **Files Replaced**: app.py, check.py, daily.py, hourly.py, train_models.py
- [ ] **Python Syntax OK**: No import errors
- [ ] **Runs Locally**: `python app.py` starts without errors
- [ ] **Settings Correct**:
  - [ ] `FLASK_ENV` = "development" (local) or "production" (Render)
  - [ ] `PORT` uses `os.environ.get("PORT", 5000)`
  - [ ] Paths use `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`
- [ ] **API Keys Set**:
  - [ ] Create `.env` file with API keys (local only!)
  - [ ] Environment variables set in Render dashboard (production)
- [ ] **Frontend Works**: Dashboard loads at http://localhost:5000
- [ ] **Predictions Work**: Test API prediction endpoint
- [ ] **Git Ready**: All changes committed and pushed

---

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'tensorflow'`
```powershell
pip install -r requirements.txt
```

### Issue: `FileNotFoundError: data/daily/BTC-INR_daily.csv`
- Files must be in correct structure
- Check: `c:\VS CODE\CryptoForecast\data\daily\` contains CSV files

### Issue: `PermissionError` when starting server
- Close previous Flask instances
- Use `lsof -i :5000` (Mac/Linux) to find process
- Or just restart PowerShell

### Issue: Models not loading on Render
- Ensure `.h5` and `.pkl` files are committed to Git
- Check Render logs: `git push` → Render → Open logs
- Verify `MODEL_DIR` path is correct

### Issue: "API key missing" error
- Add to Render Environment variables:
  - `CRYPTOPANIC_API_KEY=your_key`
  - `COINDESK_API_KEY=your_key`

---

## 📝 Files Summary

| File | Location | Purpose |
|------|----------|---------|
| app.py | ✨ Refactored | Flask server with dynamic port |
| check.py | ✨ Refactored | Predictions + lazy-load FinBERT |
| daily.py | ✨ Refactored | Download daily crypto data |
| hourly.py | ✨ Refactored | Download hourly crypto data |
| train_models.py | ✨ Refactored | Train LSTM models |
| requirements.txt | ✨ New | Python dependencies |
| Procfile | ✨ New | Render deployment config |
| .gitignore | ✨ New | Git exclusions |
| .env.example | ✨ New | Environment template |
| DEPLOYMENT.md | 📖 New | Full deployment guide |
| REFACTORING_SUMMARY.md | 📖 New | Changes overview |

---

## 🎯 Next Steps

1. **Complete Steps 1-5** above
2. **Read** `DEPLOYMENT.md` for detailed Render setup
3. **Test Prediction**: POST to `/api/predict` endpoint
4. **Deploy**: Connect GitHub repo to Render
5. **Monitor**: Check Render logs in dashboard

---

**You're all set! Deploy with confidence! 🚀**
