# EXAMPLE OUTPUT

This is what the script's output looks like when analyzing a token:

```
======================================================================
ANALYZING TOKEN: 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr
======================================================================

📊 Fetching token data from Moralis...
🔍 Fetching creator info from Bitquery...

======================================================================
RESULTS
======================================================================

Token Name: Pump Fun Token
Symbol: PUMP
Mint Address: 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr

--- PRICE & MARKET DATA ---
Current Price: $0.00005432
Market Cap: $54,320.00
Total Liquidity: $4,850.00
Number of Pools: 2

--- CREATOR INFO ---
Creator Address: 5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1
Created: 2024-11-03T15:30:00Z
Total Tokens Launched by Creator: 3

--- ASSESSMENT ---
Quality Score: MEDIUM
  ✅ Healthy liquidity ratio
  ✅ Listed on multiple pools (good sign)
  ℹ️ Creator has launched 3 tokens

======================================================================


Save analysis to file? (y/n): y
Enter filename (default: token_analysis.txt): pump_analysis.txt
✅ Analysis saved to pump_analysis.txt
```

---

## What Each Section Means

### Token Info
Basic identification - name, symbol, and the unique mint address

### Price & Market Data
- **Current Price:** What one token costs right now
- **Market Cap:** Total value if you multiply price by all tokens
- **Total Liquidity:** Real money in trading pools (MOST IMPORTANT!)
- **Number of Pools:** How many places you can trade it

### Creator Info
- **Creator Address:** The wallet that launched this token
- **Created:** When it was launched
- **Total Tokens Launched:** How many other tokens this creator made
  → If this number is high (10+), it's likely a serial scammer

### Assessment
Simple verdict based on the data:
- **Quality Score:** HIGH/MEDIUM/LOW based on multiple factors
- **Flags:** Specific warnings or positive signs

---

## Reading Between the Lines

### Example 1: Fake High Market Cap
```
Market Cap: $5,000,000
Total Liquidity: $3,000
Liquidity Ratio: 0.06%
```
**Analysis:** This is FAKE! With only $3K liquidity, you could never actually sell enough to realize that $5M cap. The creator likely held most tokens and set a high price with minimal trading.

### Example 2: Healthy Token
```
Market Cap: $250,000
Total Liquidity: $25,000
Liquidity Ratio: 10%
Number of Pools: 3
Creator Tokens: 1
```
**Analysis:** Looks legitimate! Good liquidity backing the market cap, trading on multiple pools, and the creator only made one token (not a serial launcher).

### Example 3: Serial Scammer
```
Creator Address: 8x7Yg...
Total Tokens Launched: 47
```
**Analysis:** AVOID! This creator has launched 47 tokens. They're likely creating pump-and-dump schemes repeatedly.

---

## Tips for Interpreting Results

1. **Liquidity is King**: If liquidity is <2% of market cap, be very suspicious
2. **Multiple Pools = Better**: More places to trade = more legitimate
3. **Creator History Matters**: 1-3 tokens = normal, 10+ = likely scammer
4. **Market Cap Isn't Everything**: A $10M cap means nothing without liquidity
5. **New Tokens are Risky**: Created <1 day ago? Wait and watch first

---

## What to Do After Running the Analysis

✅ **If Quality Score is HIGH:**
- Do additional research (social media, community)
- Check Dexscreener for volume trends
- Consider it for further investigation

⚠️ **If Quality Score is MEDIUM:**
- Proceed with caution
- Look for specific red flags in the assessment
- Maybe wait to see how it develops

❌ **If Quality Score is LOW:**
- Probably avoid
- If you still want to proceed, only use money you can afford to lose
- Don't ignore multiple red flags

Remember: This tool helps with due diligence, but isn't financial advice!
