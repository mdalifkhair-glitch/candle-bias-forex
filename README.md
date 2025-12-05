# Candle Bias Forex Dashboard

Multi-timeframe trend bias indicator for Forex pairs and precious metals.  
Accessible from any browser including mobile! 📱

## 🚀 Deploy to Render (Recommended)

### Step 1: Push to GitHub
1. Create a new repository on GitHub
2. Push this folder to your repository

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `candle-bias-forex` (or any name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **"Create Web Service"**

Your app will be live at: `https://your-app-name.onrender.com`

---

## Currency Pairs (11 Total)
**Forex**: EUR/USD, GBP/USD, USD/JPY, USD/CHF, USD/CAD, AUD/USD, NZD/USD  
**Metals**: XAU/USD, XAU/JPY, XAU/GBP, XAG/USD

## Bias Logic
| Bias | Condition |
|------|-----------|
| STRONG BULL | Close > Previous High |
| BULL | Low tested below, recovered above |
| NEUTRAL | Inside bar |
| BEAR | High tested above, closed below |
| STRONG BEAR | Close < Previous Low |

## API Endpoints
- `GET /` - Dashboard UI
- `GET /api/bias` - All pairs bias data
- `GET /api/health` - Health check
