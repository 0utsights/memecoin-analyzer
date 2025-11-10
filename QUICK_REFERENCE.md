# QUICK REFERENCE CARD

## Installation (One-Time Setup)
```bash
pip install requests
```

## Running the Script
```bash
python memecoin_analyzer.py
```

## API Keys Needed
1. **Moralis** (REQUIRED): https://moralis.io → Dashboard → API Keys
2. **Bitquery** (optional): https://bitquery.io → Dashboard → API Token

## Where to Find Token Addresses
- **Pump.fun tokens:** pump.fun/coin/[ADDRESS]
- **Other tokens:** solscan.io, birdeye.so, dexscreener.com

## What to Look For

### 🚩 RED FLAGS (Avoid These)
- Liquidity < 1% of market cap = FAKE VALUE
- Creator launched 10+ tokens = SERIAL SCAMMER
- Zero or tiny liquidity = CAN'T SELL
- Only 1 pool with low volume = ILLIQUID

### ✅ GOOD SIGNS (Consider These)
- Liquidity > 5% of market cap = HEALTHY
- Multiple trading pools = LEGITIMATE
- Reasonable token count from creator (1-3)
- Growing volume over time

## Quality Scores
- **HIGH** = Multiple positive indicators, likely safe
- **MEDIUM** = Mixed signals, do more research
- **LOW** = Red flags present, likely avoid

## Common Mistakes to Avoid
1. ❌ Don't trust market cap alone (can be faked)
2. ❌ Don't ignore liquidity (can't sell without it)
3. ❌ Don't skip creator research (serial scammers exist)
4. ✅ DO combine multiple metrics for assessment

## Emergency Stops
- Creator has 20+ tokens? → Probably a scammer
- Market cap $10M but only $5K liquidity? → Fake value
- Token created <1 hour ago? → Wait and watch
- No social media/community? → Suspicious

## Example Good Token Profile
- Market Cap: $500,000
- Liquidity: $50,000 (10% ratio) ✅
- Pools: 3 different DEXs ✅
- Creator tokens: 1 or 2 ✅
- Volume: Consistent daily trading ✅
- Quality Score: HIGH

## Example Bad Token Profile
- Market Cap: $5,000,000
- Liquidity: $2,000 (0.04% ratio) 🚩
- Pools: 1 low-volume pool 🚩
- Creator tokens: 47 🚩
- Volume: Sporadic/none 🚩
- Quality Score: LOW

---
Remember: Do your own research! This tool helps, but isn't financial advice.
