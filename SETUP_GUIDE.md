# Memecoin Analyzer - Setup Guide

## What This Tool Does

This Python script analyzes Solana tokens (especially Pump.fun memecoins) using multiple metrics beyond just market cap to help you identify high-value coins vs fake/scam tokens.

**Key Features:**
- Fetches real-time price, market cap, and liquidity data
- Identifies token creator and their history
- Calculates liquidity ratios to spot fake market caps
- Provides a simple quality assessment
- Saves results to a text file

---

## Prerequisites

You need:
1. **Python 3.7 or higher** installed on your computer
2. **pip** (Python package manager - usually comes with Python)

### Check if you have Python:
```bash
python --version
# or
python3 --version
```

If you don't have Python, download it from: https://www.python.org/downloads/

---

## Step 1: Get API Keys (FREE)

### Moralis API Key (REQUIRED)
1. Go to https://moralis.io
2. Click "Start for Free" and create an account
3. After logging in, go to your dashboard
4. Click on "API Keys" or "Web3 API"
5. Copy your API key (it looks like: `eyJhbGc...`)

### Bitquery API Key (OPTIONAL - for creator info)
1. Go to https://bitquery.io
2. Sign up for a free account
3. After logging in, go to your dashboard
4. Find your API token/key
5. Copy it

**Note:** The script works without Bitquery, but you won't get creator information.

---

## Step 2: Install Dependencies

Open your terminal/command prompt and navigate to the folder containing the script.

### Install required packages:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests
```

---

## Step 3: Configure the Script

Open `memecoin_analyzer.py` in any text editor (Notepad, VS Code, etc.)

Find these lines near the top (around line 10-11):
```python
MORALIS_API_KEY = "YOUR_MORALIS_API_KEY_HERE"
BITQUERY_API_KEY = "YOUR_BITQUERY_API_KEY_HERE"
```

Replace with your actual API keys:
```python
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
BITQUERY_API_KEY = "BQYxxxxxxxxxxxxxxxxxxxxx"
```

**Save the file!**

---

## Step 4: Run the Script

In your terminal/command prompt:

```bash
python memecoin_analyzer.py
```

Or on some systems:
```bash
python3 memecoin_analyzer.py
```

---

## How to Use

When you run the script, it will ask for a Solana token mint address.

### Finding Mint Addresses:

**For Pump.fun tokens:**
1. Go to pump.fun
2. Click on any token
3. Look at the URL: `pump.fun/coin/ABC123...`
4. The part after `/coin/` is the mint address

**For other Solana tokens:**
- Find them on Solscan.io, Birdeye, or Dexscreener
- They look like: `So11111111111111111111111111111111111111112`

### Example:
```
Enter a Solana token mint address to analyze:
> 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr
```

The script will then:
1. Fetch all the data from APIs
2. Calculate metrics
3. Display results in your terminal
4. Offer to save to a text file

---

## Understanding the Results

### Price & Market Data
- **Current Price:** Price per token in USD
- **Market Cap:** Total value (price × circulating supply)
- **Total Liquidity:** How much money is in trading pools
- **Number of Pools:** How many places the token can be traded

### Creator Info
- **Creator Address:** Who launched the token
- **Total Tokens Launched:** How many tokens this creator has made
  - ⚠️ If >10: Possible serial scammer
  - ✅ If 1: First-time creator (could be legit)

### Quality Assessment
The script gives a simple quality score:
- **HIGH:** Multiple positive indicators
- **MEDIUM:** Some positive, some concerning
- **LOW:** Red flags present

### Key Red Flags:
- ⚠️ **Very low liquidity vs market cap** = Likely fake/manipulated value
- ⚠️ **Creator launched many tokens** = Possible serial scammer
- ⚠️ **Zero liquidity** = Can't actually sell the token

### Good Signs:
- ✅ **Healthy liquidity ratio** (>5% of market cap)
- ✅ **Multiple trading pools** = More legitimate
- ✅ **First-time creator** = Not a serial launcher

---

## Troubleshooting

### "Error fetching metadata"
- Check that your Moralis API key is correct
- Make sure the mint address is valid
- Check your internet connection

### "Error fetching creator info"
- Your Bitquery API key might be wrong/expired
- Or you hit the free tier rate limit (wait a bit)
- The script will still work without creator info

### "ModuleNotFoundError: No module named 'requests'"
- Run: `pip install requests`

### Script won't start
- Make sure you saved the file after adding API keys
- Try: `python3 memecoin_analyzer.py` instead of `python`

---

## Advanced Usage

### Analyzing Multiple Tokens

You can modify the script to analyze multiple tokens at once. Add this at the bottom:

```python
# List of tokens to analyze
tokens = [
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    # Add more mint addresses here
]

for mint in tokens:
    analyze_token(mint, include_creator=True)
    print("\n\n")
```

### Saving All Results to One File

Modify the save function call to append instead of overwrite:
```python
# In save_analysis_to_file function, change 'w' to 'a'
with open(filename, 'a') as f:  # 'a' = append mode
```

---

## Rate Limits (Free Tiers)

**Moralis Free Tier:**
- ~100,000 requests per month
- Should be plenty for testing

**Bitquery Free Tier:**
- Limited requests per day
- If you hit the limit, wait 24 hours or upgrade

---

## Next Steps

1. Test with a few known tokens first
2. Compare results with what you see on pump.fun or Dexscreener
3. Build a list of quality tokens over time
4. Consider adding more metrics (holder count, volume trends, etc.)

---

## Need Help?

- Moralis Docs: https://docs.moralis.io
- Bitquery Docs: https://docs.bitquery.io
- Solana Explorer: https://solscan.io

Good luck finding those gems! 🚀
