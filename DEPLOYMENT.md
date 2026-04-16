# 🚀 CryptoForecast - Deployment Guide for Render

## 📋 Overview

This guide helps you deploy the CryptoForecast application to **Render** free tier.

### What's Included
- Flask backend with LSTM predictions
- TensorFlow ML models (pre-trained)
- FinBERT sentiment analysis
- Responsive frontend dashboard
- All optimized for free tier hosting

---

## 🔧 Pre-Deployment Setup (Local)

### 1. Update the Original Files

Replace your original files with the refactored versions:

```bash
# Backup originals (optional)
cp app.py app.py.backup
cp check.py check.py.backup
cp daily.py daily.py.backup
cp hourly.py hourly.py.backup
cp train_models.py train_models.py.backup

# Use the new versions
mv app_new.py app.py
mv check_new.py check.py
mv daily_new.py daily.py
mv hourly_new.py hourly.py
mv train_models_new.py train_models.py
```

### 2. Test Locally

```bash
# Set environment variables (Windows)
$env:FLASK_ENV = "development"
$env:PORT = 5000
$env:CRYPTOPANIC_API_KEY = "your_api_key"
$env:COINDESK_API_KEY = "your_api_key"

# Or create .env file
# FLASK_ENV=development
# PORT=5000
# CRYPTOPANIC_API_KEY=your_api_key
# COINDESK_API_KEY=your_api_key

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test at http://localhost:5000
```

---

## 🎯 Deploy to Render (Free Tier)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit - ready for Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/CryptoForecast.git
git push -u origin main
```

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +"  → "Web Service"

### Step 3: Configure Web Service
1. **Repository**: Connect your CryptoForecast GitHub repo
2. **Name**: `cryptoforecast`
3. **Environment**: `Python 3`
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `gunicorn app:app`
6. **Instance Type**: `Free` (or paid if needed)

### Step 4: Set Environment Variables
In Render dashboard → Environment:

```env
FLASK_ENV=production
CRYPTOPANIC_API_KEY=your_api_key_here
COINDESK_API_KEY=your_api_key_here
PORT=5000
```

**Get API Keys:**
- CryptoPanic: https://cryptopanic.com/developers/api/
- CoinDesk: https://www.coindesk.com/api/

### Step 5: Deploy
Click "Deploy" and wait for the build to complete (~5-10 minutes).

Your app will be available at: `https://cryptoforecast.onrender.com`

---

## ✅ What's Been Optimized

### 1. **Dynamic Port Configuration**
```python
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
```

### 2. **Relative File Paths**
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
```

### 3. **Environment Variables for API Keys**
```python
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "fallback_key")
```

### 4. **Lazy Loading (Memory Optimization)**
```python
_finbert = None  # Load only when needed

def get_finbert():
    global _finbert
    if _finbert is None:
        _finbert = pipeline(...)  # Load on first use
    return _finbert
```

### 5. **Model Caching**
```python
_model_cache = {}

def load_model_and_scaler(coin, mode):
    cache_key = f"{coin}_{mode}"
    if cache_key in _model_cache:
        return _model_cache[cache_key], _scaler_cache[cache_key]
    # ... load and cache
```

### 6. **Error Handling**
- API calls wrapped in try-except
- Meaningful error messages returned to frontend
- Graceful fallbacks (e.g., sentiment defaults to 0)

### 7. **Production Ready**
- Uses Gunicorn (production WSGI)
- Proper HTTP status codes (202 for async)
- Request validation
- Debug mode disabled in production

---

## 📊 Deployment Files

Your project now includes:

|File|Purpose|
|---|---|
|**requirements.txt**|All Python dependencies|
|**Procfile**|Render deployment config|
|**.gitignore**|Exclude sensitive files|
|**.env.example**|Template for environment variables|

---

## 🐛 Common Issues & Solutions

### Issue: "Module not found" errors
**Solution**: All paths use `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`

### Issue: "API key missing" 
**Solution**: Set environment variables in Render dashboard

### Issue: Models loading slowly
**Solution**: Models are now cached in memory on first load

### Issue: Out of memory (free tier)
**Solution**: Models use lazy loading, only loaded when predictions requested

---

## 📱 Testing POST Endpoints

### Test Prediction API:
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC",
    "mode": "daily",
    "timeframe": 7
  }'
```

### Check Status:
```bash
curl http://localhost:5000/api/progress/1234567890
```

### Health Check:
```bash
curl http://localhost:5000/api/health
```

---

## 📈 Performance Notes

**Render Free Tier Limits:**
- 0.5 CPU
- 512 MB RAM
- 100 GB bandwidth/month
- Auto-sleep after 15 min inactivity

**Optimizations:**
✅ Lazy loading prevents startup memory spike  
✅ Model caching reduces reload time  
✅ Async predictions don't block requests  
✅ Minimal dependencies in requirements.txt  

---

## 🔄 Updates & Data Refresh

To update cryptocurrency data:

```bash
# Run locally (not on Render during free tier)
python daily.py
python hourly.py

# Commit updated CSVs
git add data/
git commit -m "Update crypto data"
git push
```

Models are pre-trained and won't change unless you retrain.

---

## ✨ Features Preserved

✅ LSTM price predictions (hourly & daily)  
✅ FinBERT sentiment analysis  
✅ TensorFlow neural networks  
✅ Real-time charts  
✅ User authentication UI  
✅ Responsive dark/light theme  
✅ All 10 cryptocurrencies  

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Flask Docs**: https://flask.palletsprojects.com
- **Gunicorn Docs**: https://gunicorn.org

---

**Ready to deploy?** Push to GitHub and connect to Render! 🚀
