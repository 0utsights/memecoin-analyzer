"""
Memecoin Analyzer - Streamlined Version
"""

import sys
import requests
import json
from datetime import datetime

# Configure UTF-8 encoding for Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# API Configuration
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjcxYzg2ZGE0LThkNGItNDUxNC04Mzg3LWU5OTc1NTg5MDBmOSIsIm9yZ0lkIjoiNDc5NzExIiwidXNlcklkIjoiNDkzNTIxIiwidHlwZUlkIjoiM2Q3YWZlNzctZDgyYi00YmViLTlmNTktOWQxODJmY2E4MWY2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NjIzNjY2NDksImV4cCI6NDkxODEyNjY0OX0.62te1Lb_z2ghBHWKvWcJMM387y_M2ZrNvLROG1wyx7c"
BITQUERY_API_KEY = "ory_at_wg32I_QQLQ8fNwQ1bDLv9fnBxecVegyX7tocxInT55Y.2Cxc952dQ3v5gRNk-mvLAZHNxi-ooKCPLeCXZ5EeGiE"

MORALIS_BASE_URL = "https://solana-gateway.moralis.io"
BITQUERY_URL = "https://streaming.bitquery.io/graphql"

# Helper Functions
def parse_abbreviated_number(value):
    """
    Parse numbers that may have K/M/B suffixes or be regular numbers.
    Examples: "4B" -> 4000000000, "100M" -> 100000000, "50K" -> 50000, "1234.56" -> 1234.56
    """
    if value is None:
        return 0

    # Convert to string if not already
    value_str = str(value).strip()

    # Handle empty strings
    if not value_str:
        return 0

    # Check for suffix
    suffixes = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}

    # Get the last character
    last_char = value_str[-1].upper()

    if last_char in suffixes:
        # Extract the numeric part
        try:
            numeric_part = float(value_str[:-1])
            return numeric_part * suffixes[last_char]
        except ValueError:
            # If parsing fails, try to parse the whole thing as a number
            pass

    # Try to parse as a regular number
    try:
        return float(value_str)
    except ValueError:
        return 0

# API Functions
def get_token_metadata(mint):
    url = f"{MORALIS_BASE_URL}/token/mainnet/{mint}/metadata"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_token_price(mint):
    url = f"{MORALIS_BASE_URL}/token/mainnet/{mint}/price"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_token_pairs(mint):
    url = f"{MORALIS_BASE_URL}/token/mainnet/{mint}/pairs"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not fetch pairs data - {e}")
        return None
    except Exception as e:
        print(f"Warning: Error parsing pairs data - {e}")
        return None

def get_token_creator(mint):
    if BITQUERY_API_KEY == "YOUR_BITQUERY_API_KEY_HERE":
        return None
    
    query = """
    query TokenCreator($mint: String!) {
      Solana {
        Instructions(
          where: {
            Instruction: {
              Program: {
                Method: {is: "create"}
                Address: {is: "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}
              }
            }
            Transaction: {Result: {Success: true}}
          }
          limit: {count: 1}
        ) {
          Transaction {Signer}
          Block {Time}
        }
      }
    }
    """
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BITQUERY_API_KEY}"}
    payload = {"query": query, "variables": {"mint": mint}}
    
    try:
        response = requests.post(BITQUERY_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_creator_token_count(creator_address):
    if BITQUERY_API_KEY == "YOUR_BITQUERY_API_KEY_HERE":
        return None
    
    query = """
    query CreatorTokens($creator: String!) {
      Solana {
        Instructions(
          where: {
            Instruction: {
              Program: {
                Method: {is: "create"}
                Address: {is: "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}
              }
            }
            Transaction: {
              Signer: {is: $creator}
              Result: {Success: true}
            }
          }
        ) {count}
      }
    }
    """
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BITQUERY_API_KEY}"}
    payload = {"query": query, "variables": {"creator": creator_address}}
    
    try:
        response = requests.post(BITQUERY_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['data']['Solana']['Instructions'][0]['count']
    except:
        return None

# Analysis
def analyze_token(mint):
    print("="*70)
    print(f"ANALYZING: {mint}")
    print("="*70 + "\n")
    
    metadata = get_token_metadata(mint)
    price_data = get_token_price(mint)
    pairs_data = get_token_pairs(mint)
    
    if not metadata or not price_data:
        print("❌ Could not fetch token data\n")
        return
    
    # Calculate metrics
    name = metadata.get('name', 'Unknown')
    symbol = metadata.get('symbol', '???')
    decimals = metadata.get('decimals', 9)
    price = float(price_data.get('usdPrice', 0))

    # Get market cap from fullyDilutedValue or calculate from supply and price
    market_cap_raw = metadata.get('fullyDilutedValue')
    if market_cap_raw:
        market_cap = parse_abbreviated_number(market_cap_raw)
    else:
        # Fallback: calculate from total supply and price
        total_supply = metadata.get('totalSupplyFormatted', metadata.get('totalSupply', '1000000000'))
        try:
            supply = float(total_supply)
        except (ValueError, TypeError):
            supply = 1_000_000_000  # Default to 1 billion if can't parse
        market_cap = supply * price
    
    total_liquidity = 0
    num_pools = 0
    if pairs_data:
        # Handle different API response structures
        pairs_list = pairs_data

        # If pairs_data is a dict with a 'pairs' key, extract the list
        if isinstance(pairs_data, dict):
            pairs_list = pairs_data.get('pairs', pairs_data.get('data', []))

        # Ensure we have a list
        if not isinstance(pairs_list, list):
            pairs_list = []

        for pair in pairs_list:
            # Skip if pair is not a dictionary (defensive coding)
            if not isinstance(pair, dict):
                continue

            # Try to get liquidity from different possible structures
            liq = 0

            # Check for liquidityUsd (Moralis Solana format)
            if 'liquidityUsd' in pair:
                liq = pair.get('liquidityUsd', 0)
            # Check for nested liquidity.usd structure (some APIs)
            elif 'liquidity' in pair:
                liquidity_data = pair.get('liquidity', {})
                if isinstance(liquidity_data, dict):
                    liq = liquidity_data.get('usd', 0)
                elif isinstance(liquidity_data, (int, float)):
                    liq = liquidity_data

            if liq:
                total_liquidity += float(liq)

        num_pools = len([p for p in pairs_list if isinstance(p, dict)])
    
    liquidity_ratio = (total_liquidity / market_cap * 100) if market_cap > 0 else 0
    
    # Creator info
    creator_info = get_token_creator(mint)
    creator_address = None
    creator_tokens = None
    
    if creator_info and 'data' in creator_info:
        instructions = creator_info['data']['Solana']['Instructions']
        if instructions:
            creator_address = instructions[0]['Transaction']['Signer']
            creator_tokens = get_creator_token_count(creator_address)
    
    # Display
    print(f"🪙 {name} (${symbol})")
    print(f"Mint: {mint}\n")
    
    print("💰 METRICS")
    print(f"  Price: ${price:.8f}")
    print(f"  Market Cap: ${market_cap:,.2f}")
    print(f"  Liquidity: ${total_liquidity:,.2f} ({liquidity_ratio:.1f}%)")
    print(f"  Pools: {num_pools}\n")
    
    if creator_address:
        print("👤 CREATOR")
        print(f"  Address: {creator_address}")
        if creator_tokens is not None:
            print(f"  Total Tokens: {creator_tokens}\n")
    
    # Assessment
    print("📊 ASSESSMENT")
    flags = []
    score = 0
    
    if total_liquidity < 5000:
        flags.append("⚠️ Low liquidity")
    elif total_liquidity > 10000:
        flags.append("✅ Good liquidity")
        score += 2
    else:
        score += 1
    
    if liquidity_ratio < 2:
        flags.append("⚠️ Poor liquidity ratio (possible fake market cap)")
    elif liquidity_ratio > 5:
        flags.append("✅ Healthy liquidity ratio")
        score += 2
    else:
        score += 1
    
    if num_pools > 1:
        flags.append("✅ Multiple pools")
        score += 1
    elif num_pools == 0:
        flags.append("❌ No pools found")
    
    if creator_tokens is not None:
        if creator_tokens > 10:
            flags.append(f"⚠️ Serial launcher ({creator_tokens} tokens)")
        elif creator_tokens <= 3:
            flags.append(f"✅ Creator OK ({creator_tokens} tokens)")
            score += 1
    
    quality = "HIGH" if score >= 4 else "MEDIUM" if score >= 2 else "LOW"
    print(f"  Quality: {quality}")
    for flag in flags:
        print(f"  {flag}")
    
    print("\n" + "="*70 + "\n")

# Main
if __name__ == "__main__":
    print("🚀 Memecoin Analyzer\n")
    
    mint = input("Enter token mint address: ").strip()
    if not mint:
        mint = "So11111111111111111111111111111111111111112"
    
    analyze_token(mint)
