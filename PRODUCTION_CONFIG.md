# 🎬 PRODUCTION CONFIGURATION GUIDE

## 📋 Quick Reference

| Setting | Development | Production (Render) |
|---------|-------------|-------------------|
| FLASK_ENV | `development` | `production` |
| DEBUG | `True` | `False` |
| PORT | `5000` (local) | Dynamic (env var) |
| Host | `localhost` | `0.0.0.0` |
| Server | Flask | Gunicorn |
| API Keys | `.env` file | Environment vars |

---

## 🔑 Environment Variables

### Required for Both Dev & Production

```env
# Crypto API Keys (Get from official sources)
CRYPTOPANIC_API_KEY=your_cryptopanic_token
COINDESK_API_KEY=your_coindesk_token

# Flask Configuration
FLASK_ENV=production              # "development" or "production"
PORT=5000                         # Dynamic on Render
```

### Optional

```env
# Maximum prediction steps (safety limit)
MAX_PREDICTION_STEPS=168
MAX_TIMEFRAME=365

# Sentiment analysis
ENABLE_SENTIMENT=true
FINBERT_BATCH_SIZE=8
```

---

## 🏠 Local Development Setup

### 1. Create `.env` File

```bash
cd "c:\VS CODE\CryptoForecast"
```

Create file `.env`:
```env
FLASK_ENV=development
PORT=5000
CRYPTOPANIC_API_KEY=demo_key_if_testing
COINDESK_API_KEY=demo_key_if_testing
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run Server

```powershell
python app.py
```

**Output:**
```
🚀 CryptoForeCast Server Starting
   Port: 5000
   Debug: True
   Host: 0.0.0.0
 * Running on http://127.0.0.1:5000
```

### 4. Test Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Make prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC","mode":"daily","timeframe":7}'

# Check progress
curl http://localhost:5000/api/progress/{prediction_id}
```

---

## 🌐 Render Production Setup

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up with GitHub

### 2. Connect Repository
- Click "New +" → "Web Service"
- Select GitHub repo: `CryptoForecast`
- Connect authorization

### 3. Configure Web Service

| Field | Value |
|-------|-------|
| Name | `cryptoforecast` |
| Region | Choose closest to users |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | `Free` (or upgrade if needed) |

### 4. Set Environment Variables

Go to **Environment** tab and add:

```env
FLASK_ENV=production
CRYPTOPANIC_API_KEY=your_actual_key_here
COINDESK_API_KEY=your_actual_key_here
```

**To get API Keys:**

#### CryptoPanic API
1. Visit: https://cryptopanic.com/developers/api/
2. Sign up for free
3. Create API key
4. Copy token

#### CoinDesk API  
1. Visit: https://www.coindesk.com/api/
2. No signup needed (free tier)
3. Use default public key

### 5. Deploy

- Click **Deploy**
- Wait for build (3-5 minutes)
- View live URL: `https://your-service-name.onrender.com`

### 6. Test Production

```bash
# Health check
curl https://your-service-name.onrender.com/api/health

# Full prediction test
curl -X POST https://your-service-name.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol":"ETH","mode":"hourly","timeframe":12}'
```

---

## 📊 Performance Monitoring

### Render Dashboard
- **Logs**: View real-time application logs
- **Metrics**: CPU, Memory, Network usage
- **Activity**: Deployment history

### Key Metrics to Watch
- **Cold starts**: ~5-10 seconds on free tier
- **Memory usage**: Should stay under 300 MB
- **Response time**: <5 seconds for predictions

### Optimization Commands

```bash
# Check Render logs
# Dashboard → Logs (live stream)

# Redeploy latest commit
# Dashboard → Manual Deploy

# View environment variables
# Dashboard → Environment (verify all set)
```

---

## 🔒 Security Checklist

- [ ] **API Keys Protected**
  - ✅ Not in source code
  - ✅ Only in `.env.example` template
  - ✅ Real keys in Render dashboard only

- [ ] **CORS Enabled**
  - ✅ `CORS(app)` allows cross-origin requests
  - ✅ Necessary for frontend-backend communication

- [ ] **Git Safe**
  - ✅ `.gitignore` excludes `.env`
  - ✅ `.gitignore` excludes `__pycache__`
  - ✅ Never commit `backup/` folder

- [ ] **Errors Sanitized**
  - ✅ Error messages don't expose paths
  - ✅ Generic errors in production

---

## 🚀 Deployment Workflow

### Local Development Cycle
```bash
# 1. Make changes
# 2. Test locally
python app.py
curl http://localhost:5000/api/health

# 3. Commit
git add .
git commit -m "Feature: Add X"

# 4. Push
git push origin main

# 5. Render auto-deploys
# (Watch: Dashboard → Logs)
```

### Update Cryptocurrency Data
```bash
# Local only (do NOT run on Render free tier)
python daily.py
python hourly.py

# Commit updates
git add data/
git commit -m "chore: Update crypto data"
git push origin main
```

---

## ⚠️ Known Limitations (Free Tier)

1. **Cold Start**: First request after 15 min takes 5-10 seconds
2. **Memory Cap**: 512 MB - models cached in memory
3. **Disk Space**: Limited - CSV files OK, don't add large files
4. **Bandwidth**: 100 GB/month (plenty for predictions)
5. **CPU**: 0.5 vCPU - predictions may be slow for many requests

### Workarounds
- ✅ Use model caching to reduce memory reboots
- ✅ Lazy-load FinBERT only when sentiment needed
- ✅ Async predictions don't block requests
- ✅ Scale to paid to bypass limitations

---

## 📈 Upgrading from Free Tier

If you exceed free tier limits:

1. **Starter Plan** ($7/month)
   - 1 GB RAM
   - Always on (no cold starts)
   - 250 build minutes/month

2. **Standard Plan** ($12/month)
   - 2 GB RAM
   - Dedicated resources
   - Priority support

**Upgrade in Render Dashboard → Plan**

---

## 🆘 Troubleshooting

### "Build failed"
1. Check `FLASK_ENV` is set
2. Verify `requirements.txt` exists
3. Check Python 3.9+ compatible packages
4. View full build log in Render

### "Module not found" (runtime)
1. Reinstall dependencies locally: `pip install -r requirements.txt`
2. Update `requirements.txt`: `pip freeze > requirements.txt`
3. Push and redeploy

### "API returns 502 Bad Gateway"
1. Models loading (first request after sleep)
2. Memory limit exceeded
3. Check Render logs for errors
4. Ensure API keys are set

### "Predictions are slow"
1. First request after 15 min = cold start
2. Free tier only has 0.5 vCPU
3. Check Render metrics
4. Consider upgrading

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Flask Docs**: https://flask.palletsprojects.com
- **Gunicorn Docs**: https://gunicorn.org
- **TensorFlow**: https://tensorflow.org
- **Status Page**: https://status.render.com

---

**🎉 Your app is production-ready!**
