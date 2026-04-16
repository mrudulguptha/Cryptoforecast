# 🚀 QUICK START - 5 Steps to Deploy

## Step 1: Replace Files (2 min)

```powershell
cd "c:\VS CODE\CryptoForecast"

# Backup (optional but recommended)
mkdir backup
cp app.py, check.py, daily.py, hourly.py, train_models.py backup/

# Replace with new versions
mv app_new.py app.py -Force
mv check_new.py check.py -Force
mv daily_new.py daily.py -Force
mv hourly_new.py hourly.py -Force
mv train_models_new.py train_models.py -Force
```

## Step 2: Install Dependencies (3 min)

```powershell
pip install -r requirements.txt
```

## Step 3: Test Locally (5 min)

```powershell
# Set mode to development
$env:FLASK_ENV = "development"

# Run
python app.py

# Open browser → http://localhost:5000
# Test prediction from dashboard

# Stop server → CTRL+C
```

## Step 4: Push to GitHub (2 min)

```powershell
git add .
git commit -m "refactor: Deploy-ready optimization for Render"
git push origin main
```

## Step 5: Deploy on Render (5 min)

1. Go to **render.com**
2. Sign up with GitHub
3. Click **New +** → **Web Service**
4. Select your repo
5. Fill form:
   - Name: `cryptoforecast`
   - Runtime: `Python 3`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
6. Add **Environment Variables**:
   ```
   FLASK_ENV=production
   CRYPTOPANIC_API_KEY=your_key
   COINDESK_API_KEY=your_key
   ```
7. Click **Deploy**
8. Wait 5-10 minutes
9. Visit your live URL! 🎉

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `README_REFACTOR.md` | 📖 Complete overview |
| `DEPLOYMENT.md` | 📖 Detailed Render steps |
| `MIGRATION_CHECKLIST.md` | ✅ File replacement steps |
| `PRODUCTION_CONFIG.md` | ⚙️ Security & config |
| `REFACTORING_SUMMARY.md` | 📋 What changed |

---

## 🔑 Get API Keys

### CryptoPanic (Free)
- Visit: https://cryptopanic.com/developers/api/
- Sign up → Create API key → Copy

### CoinDesk (Free)
- https://www.coindesk.com/api/ (no signup needed)

---

## ✅ What Works

✅ Predictions (daily & hourly)  
✅ Sentiment analysis  
✅ 10 cryptocurrencies  
✅ Dashboard UI  
✅ Charts  
✅ Dark/Light mode  

---

## 📊 Render Free Tier

- 512 MB RAM
- 0.5 vCPU
- Auto-sleep (5-10s cold start)
- 100 GB bandwidth/month
- **Completely FREE** ✅

---

## 🐛 Common Issues

**"Module not found"**
```powershell
pip install -r requirements.txt
```

**"Port already in use"**
- Close other Flask instances
- Or use different port: `$env:PORT = "5001"`

**"Models/data not found"**
- Ensure files are in `models/` and `data/` folders
- Check path structure

**"API key invalid"**
- Set in Render Environment variables
- Not in code (kept in `.env` locally)

---

## 🎯 Status

| Item | Status |
|------|--------|
| Code Refactored | ✅ |
| Files Config | ✅ |
| Dependencies | ✅ |
| Documentation | ✅ |
| Ready to Deploy | ✅ |

---

**You're all set! Follow 5 steps above and you'll be live in 20 minutes! 🚀**
