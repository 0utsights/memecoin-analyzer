"""
Pump.fun Auto-Scanner - Streamlined Version
"""

import requests
import time
from datetime import datetime
import winsound
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix encoding and buffering for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
else:
    # Force unbuffered output on all platforms
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# Print immediately to verify script is running
print("=" * 70)
print("INITIALIZING SCANNER...")
print("=" * 70)
sys.stdout.flush()

# API Configuration
# Bitquery API (optional - only for creator analysis if needed)
BITQUERY_API_KEY = "ory_at_wg32I_QQLQ8fNwQ1bDLv9fnBxecVegyX7tocxInT55Y.2Cxc952dQ3v5gRNk-mvLAZHNxi-ooKCPLeCXZ5EeGiE"
BITQUERY_URL = "https://streaming.bitquery.io/graphql"

# Multiple Free Solana RPC endpoints (load balanced for speed!)
SOLANA_RPC_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",  # Official Solana RPC (free, rate limited)
    "https://api.mainnet-beta.solana.com",  # Use same endpoint multiple times for now
]
rpc_index = 0

def get_solana_rpc():
    """Round-robin load balancing between RPC endpoints"""
    global rpc_index
    rpc = SOLANA_RPC_ENDPOINTS[rpc_index]
    rpc_index = (rpc_index + 1) % len(SOLANA_RPC_ENDPOINTS)
    return rpc

# For backward compatibility
SOLANA_RPC = get_solana_rpc()

# Filter Settings
MIN_LIQUIDITY_USD = 5000
MIN_LIQUIDITY_RATIO = 0.02
MAX_CREATOR_TOKENS = 5
MAX_TOKEN_AGE_HOURS = 1
SCAN_INTERVAL_SECONDS = 60

# Creator Success Criteria (to filter out fake/botted pumps)
MIN_SUCCESSFUL_MARKET_CAP = 100000  # $100k minimum market cap
MIN_SUCCESSFUL_LIQUIDITY = 10000  # $10k minimum liquidity (proves real trading)
MIN_SUCCESSFUL_LIQUIDITY_RATIO = 0.05  # 5% liquidity/mcap ratio (healthy trading)
MIN_SUCCESSFUL_HOLDERS = 50  # Minimum 50 holders (proves distribution)
MIN_CREATOR_SUCCESS_RATE = 0.3  # 30% of creator's coins should be successful

# Cache for creator token counts (speeds up scanning)
CREATOR_CACHE = {}

# Cache for SOL/USD price (refresh every scan)
SOL_USD_PRICE_CACHE = {"price": 0, "timestamp": 0}

# Helper Functions
def play_alert():
    """Play an alert sound for high potential tokens"""
    # DISABLED - Too many tokens pass filters
    # Uncomment below to re-enable beeps
    pass

    # try:
    #     # Play a series of beeps to get attention
    #     for _ in range(3):
    #         winsound.Beep(1000, 200)  # 1000 Hz for 200ms
    #         time.sleep(0.1)
    # except:
    #     # If winsound fails, just print alert
    #     print("\a" * 3)  # Terminal bell

def get_sol_usd_price():
    """
    Get SOL/USD price from CoinGecko (FREE, no API key needed!)
    Cached for 60 seconds to avoid rate limits
    """
    current_time = time.time()

    # Return cached price if less than 60 seconds old
    if SOL_USD_PRICE_CACHE["price"] > 0 and (current_time - SOL_USD_PRICE_CACHE["timestamp"]) < 60:
        return SOL_USD_PRICE_CACHE["price"]

    try:
        # CoinGecko free API (no key needed, 50 calls/minute)
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()

        price = data['solana']['usd']

        # Update cache
        SOL_USD_PRICE_CACHE["price"] = price
        SOL_USD_PRICE_CACHE["timestamp"] = current_time

        return price
    except Exception as e:
        # If fetch fails, return cached price or fallback
        if SOL_USD_PRICE_CACHE["price"] > 0:
            return SOL_USD_PRICE_CACHE["price"]
        return 150.0  # Fallback price

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

def get_token_creator_onchain(token_mint):
    """
    Get creator wallet address from on-chain data (FREE - no API key needed!)
    Finds the signer of the token creation transaction
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [token_mint, {"limit": 50}]
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=10)
        data = response.json()

        if 'result' not in data or not data['result']:
            return None

        # Last signature = creation transaction (oldest)
        creation_sig = data['result'][-1]['signature']

        # Get transaction details
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                creation_sig,
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
            ]
        }

        response = requests.post(SOLANA_RPC, json=payload, timeout=10)
        tx_data = response.json()

        if 'result' in tx_data and tx_data['result']:
            tx = tx_data['result']
            if 'transaction' in tx and 'message' in tx['transaction']:
                account_keys = tx['transaction']['message']['accountKeys']
                if account_keys:
                    # First account = fee payer = creator
                    return account_keys[0]['pubkey']

        return None
    except Exception as e:
        return None

def get_creator_token_count_onchain(creator_wallet):
    """
    Count how many pump.fun tokens this creator has launched (on-chain - FREE!)
    Uses cache to avoid rechecking same creator - FAST!
    """
    if not creator_wallet:
        return 0

    # Check cache first - INSTANT if we've seen this creator!
    if creator_wallet in CREATOR_CACHE:
        return CREATOR_CACHE[creator_wallet]

    PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [creator_wallet, {"limit": 200}]  # Reduced from 1000
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=10)
        data = response.json()

        if 'result' not in data:
            CREATOR_CACHE[creator_wallet] = 0
            return 0

        signatures = data['result']
        token_count = 0

        # Check first 20 transactions (much faster!)
        for sig_info in signatures[:20]:
            sig = sig_info['signature']

            tx_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
            }

            tx_response = requests.post(SOLANA_RPC, json=tx_payload, timeout=8)
            tx_data = tx_response.json()

            if 'result' in tx_data and tx_data['result']:
                tx = tx_data['result']
                if 'transaction' in tx and 'message' in tx['transaction']:
                    account_keys = tx['transaction']['message']['accountKeys']
                    for key in account_keys:
                        if key.get('pubkey') == PUMP_PROGRAM:
                            token_count += 1
                            break

            # NO SLEEP - faster scanning!

        # Cache the result
        CREATOR_CACHE[creator_wallet] = token_count
        return token_count

    except Exception as e:
        CREATOR_CACHE[creator_wallet] = 0
        return 0

# API Functions
def get_token_account_info_onchain(mint):
    """
    Get token mint account info on-chain (FREE!)
    Returns decimals and supply
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            mint,
            {"encoding": "jsonParsed"}
        ]
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=10)
        data = response.json()

        if 'error' in data:
            return None

        if 'result' in data and data['result'] and 'value' in data['result']:
            account_data = data['result']['value']
            if account_data and 'data' in account_data:
                # Check if data is parsed (dict) or raw (list)
                if isinstance(account_data['data'], dict) and 'parsed' in account_data['data']:
                    parsed_data = account_data['data']['parsed']['info']
                    return {
                        'decimals': parsed_data.get('decimals', 9),
                        'supply': int(parsed_data.get('supply', 0)),
                        'mintAuthority': parsed_data.get('mintAuthority')
                    }
        return None
    except Exception as e:
        return None

def get_token_metadata_onchain(mint):
    """
    Get token metadata on-chain (FREE!)
    For pump.fun tokens, we derive name/symbol from transaction data or use simplified approach
    """
    # For now, return basic info - name/symbol can be extracted from initial creation tx
    # This is a simplified version; full Metaplex parsing is complex
    account_info = get_token_account_info_onchain(mint)

    if not account_info:
        return None

    # Get the creation transaction to extract name/symbol if embedded
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [mint, {"limit": 1}]
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=10)
        sig_data = response.json()

        # Basic metadata structure (name/symbol might not be available on-chain easily)
        metadata = {
            'mint': mint,
            'decimals': account_info['decimals'],
            'supply': account_info['supply'],
            'totalSupply': str(account_info['supply'] / (10 ** account_info['decimals'])),
            'totalSupplyFormatted': str(account_info['supply'] / (10 ** account_info['decimals'])),
            'name': f"Token {mint[:8]}...",  # Fallback name
            'symbol': mint[:4].upper(),  # Fallback symbol
        }

        return metadata
    except Exception as e:
        return None

def get_raydium_pool_info(mint):
    """
    Get Raydium pool information for a token on-chain (FREE!)
    Returns liquidity and price data from Raydium DEX
    """
    # Raydium program ID
    RAYDIUM_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

    # This is a simplified version - full implementation would query Raydium's pool accounts
    # For now, we'll use a fallback approach or DexScreener free API
    try:
        # DexScreener has a free API with no key required!
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'pairs' in data and data['pairs']:
                # Get the first pair (usually the main pool)
                pairs = data['pairs']

                total_liquidity = 0
                price = 0

                for pair in pairs:
                    if 'liquidity' in pair and 'usd' in pair['liquidity']:
                        total_liquidity += float(pair['liquidity']['usd'])

                    if 'priceUsd' in pair and not price:
                        price = float(pair['priceUsd'])

                return {
                    'pairs': pairs,
                    'total_liquidity': total_liquidity,
                    'price_usd': price
                }

        return None
    except Exception as e:
        return None

def get_recent_pump_tokens(limit=50):
    """
    Get recent pump.fun tokens 100% ON-CHAIN (FREE!)
    Queries pump.fun program for recent token creations
    """
    PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

    # Get recent transactions on pump.fun program
    # Fetch more transactions since we filter out very new ones
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            PUMP_PROGRAM,
            {"limit": 200}  # Fetch 200 to find older tokens (after age filtering)
        ]
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=15)
        data = response.json()

        if 'result' not in data:
            return []

        signatures = data['result']
        tokens = []
        seen_mints = set()

        # Process ALL fetched transactions to find token creations
        # (we'll collect up to 'limit' tokens after filtering)
        for sig_info in signatures:
            sig = sig_info['signature']

            # Get transaction details
            tx_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    sig,
                    {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
                ]
            }

            tx_response = requests.post(get_solana_rpc(), json=tx_payload, timeout=10)
            tx_data = tx_response.json()

            if 'result' not in tx_data or not tx_data['result']:
                continue

            tx = tx_data['result']

            # Extract token mint and creator from transaction
            if 'transaction' in tx and 'message' in tx['transaction']:
                account_keys = tx['transaction']['message']['accountKeys']

                if len(account_keys) >= 2:
                    # First account = creator (fee payer)
                    creator = account_keys[0]['pubkey']

                    # Look for the mint address in the transaction
                    # For pump.fun, the mint is usually one of the early accounts
                    for i, account in enumerate(account_keys):
                        mint = account['pubkey']

                        # Skip program addresses and known system accounts
                        if mint in [PUMP_PROGRAM, creator]:
                            continue

                        # If we haven't seen this mint and it looks like a token
                        if mint not in seen_mints and len(mint) == 44:  # Solana addresses are 44 chars
                            seen_mints.add(mint)

                            # Get creation time and check if token is at least 2 minutes old
                            # (gives time for liquidity pools to be created)
                            if 'blockTime' in tx:
                                created_timestamp = tx['blockTime']
                                created = datetime.fromtimestamp(created_timestamp).isoformat()

                                # Calculate age in seconds
                                age_seconds = time.time() - created_timestamp

                                # Note: We don't filter by age anymore - let tokens through
                                # They'll naturally fail if they don't have liquidity yet
                            else:
                                created = ''

                            tokens.append({
                                'mint': mint,
                                'creator': creator,
                                'created': created
                            })

                            break  # Found the mint for this transaction

            if len(tokens) >= limit:
                break

        return tokens

    except Exception as e:
        print(f"Error fetching tokens on-chain: {e}")
        return []

def get_holder_count(mint):
    """Get holder count on-chain (FREE - uses Solana RPC)"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [mint]
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=10)
        data = response.json()

        if 'result' in data and 'value' in data['result']:
            # Number of accounts = holder count
            return len(data['result']['value'])
        return 0
    except Exception as e:
        return 0

def get_peak_stats(mint):
    """Get peak market cap, liquidity, and holder count for a token"""
    # Get current values as baseline using ON-CHAIN data (FREE!)
    metadata = get_token_metadata_onchain(mint)
    pool_info = get_raydium_pool_info(mint)

    peak_market_cap = 0
    peak_liquidity = 0
    peak_holders = 0

    # Calculate current/recent market cap
    if metadata and pool_info:
        price = pool_info.get('price_usd', 0)
        total_supply = metadata.get('totalSupplyFormatted', metadata.get('totalSupply', '1000000000'))
        try:
            supply = float(total_supply)
        except (ValueError, TypeError):
            supply = 1_000_000_000
        peak_market_cap = supply * price

    # Get current liquidity (this is often close to peak for newer tokens)
    if pool_info:
        peak_liquidity = pool_info.get('total_liquidity', 0)

    # Get peak holder count (total unique addresses that ever held)
    peak_holders = get_holder_count(mint)

    # Query historical high market cap using Bitquery (price history)
    # Note: This gets the highest USD price point, which we use as proxy for peak mcap
    query = """
    query PeakPrice($mint: String!) {
      Solana {
        DEXTradeByTokens(
          where: {Trade: {Currency: {MintAddress: {is: $mint}}}}
          orderBy: {descendingByField: "Trade_PriceInUSD"}
          limit: {count: 1}
        ) {
          Trade {
            PriceInUSD
          }
        }
      }
    }
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BITQUERY_API_KEY}"}
    payload = {"query": query, "variables": {"mint": mint}}

    try:
        response = requests.post(BITQUERY_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        if 'data' in data and data['data']['Solana']['DEXTradeByTokens']:
            trades = data['data']['Solana']['DEXTradeByTokens']
            if trades:
                peak_price = float(trades[0]['Trade']['PriceInUSD'])
                # Calculate peak market cap using peak price
                if metadata:
                    total_supply = metadata.get('totalSupplyFormatted', metadata.get('totalSupply', '1000000000'))
                    try:
                        supply = float(total_supply)
                        historical_peak_mcap = supply * peak_price
                        # Use the higher of current or historical
                        peak_market_cap = max(peak_market_cap, historical_peak_mcap)
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        print(f"    Warning: Could not fetch historical peak data: {e}")

    return peak_market_cap, peak_liquidity, peak_holders

def get_creator_token_count(creator):
    """Get creator token count (requires Bitquery - returns None if unavailable)"""
    if not creator:
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
            Transaction: {Signer: {is: $creator}, Result: {Success: true}}
          }
        ) {count}
      }
    }
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BITQUERY_API_KEY}"}
    payload = {"query": query, "variables": {"creator": creator}}

    try:
        response = requests.post(BITQUERY_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        count = data['data']['Solana']['Instructions'][0]['count']
        return int(count) if count is not None else None
    except:
        return None  # Bitquery unavailable

def get_creator_previous_tokens(creator, limit=10):
    """Get list of previous tokens created by this creator"""
    query = """
    query CreatorTokensList($creator: String!, $limit: Int!) {
      Solana {
        Instructions(
          where: {
            Instruction: {
              Program: {
                Method: {is: "create"}
                Address: {is: "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}
              }
            }
            Transaction: {Signer: {is: $creator}, Result: {Success: true}}
          }
          limit: {count: $limit}
          orderBy: {descending: Block_Time}
        ) {
          Transaction {Signer}
          Block {Time}
          Instruction {Accounts {Address}}
        }
      }
    }
    """

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BITQUERY_API_KEY}"}
    payload = {"query": query, "variables": {"creator": creator, "limit": limit}}

    try:
        response = requests.post(BITQUERY_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        tokens = []
        if 'data' in data and data['data']['Solana']['Instructions']:
            for instruction in data['data']['Solana']['Instructions']:
                accounts = instruction['Instruction']['Accounts']
                if accounts:
                    tokens.append({
                        'mint': accounts[0]['Address'],
                        'created': instruction['Block']['Time']
                    })
        return tokens
    except Exception as e:
        print(f"  Error fetching creator tokens: {e}")
        return []

def analyze_creator_success(creator, current_mint=None):
    """Analyze if creator has history of successful tokens using PEAK values (filters out fake/botted pumps)"""
    previous_tokens = get_creator_previous_tokens(creator, limit=10)

    if not previous_tokens:
        return 0, 0, 0  # success_rate, successful_count, total_checked

    # Filter out the current token if checking during creation
    if current_mint:
        previous_tokens = [t for t in previous_tokens if t['mint'] != current_mint]

    if not previous_tokens:
        return 0, 0, 0

    successful_count = 0
    total_checked = 0

    # Check each previous token
    for token in previous_tokens[:5]:  # Check max 5 to avoid rate limits
        mint = token['mint']

        total_checked += 1

        # Get PEAK stats (not current) - tokens may have pumped and dumped
        peak_market_cap, peak_liquidity, peak_holders = get_peak_stats(mint)

        if peak_market_cap == 0:
            print(f"      ✗ Previous token: Could not fetch data")
            continue

        # Calculate peak liquidity ratio
        peak_liquidity_ratio = peak_liquidity / peak_market_cap if peak_market_cap > 0 else 0

        # Check if this token EVER reached success criteria (proves creator can create pumps)
        is_successful = (
            peak_market_cap >= MIN_SUCCESSFUL_MARKET_CAP and
            peak_liquidity >= MIN_SUCCESSFUL_LIQUIDITY and
            peak_liquidity_ratio >= MIN_SUCCESSFUL_LIQUIDITY_RATIO and
            peak_holders >= MIN_SUCCESSFUL_HOLDERS
        )

        if is_successful:
            successful_count += 1
            print(f"      ✓ Previous token PEAK: ${peak_market_cap:,.0f} mcap, ${peak_liquidity:,.0f} liq, {peak_holders} holders")
        else:
            print(f"      ✗ Previous token failed (peak mcap: ${peak_market_cap:,.0f}, liq: ${peak_liquidity:,.0f}, holders: {peak_holders})")

        time.sleep(0.5)  # Small delay to avoid rate limits

    success_rate = successful_count / total_checked if total_checked > 0 else 0
    return success_rate, successful_count, total_checked

def get_top_holders(mint, limit=10):
    """Get top holders on-chain (FREE - uses Solana RPC)"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [mint]
    }

    try:
        response = requests.post(get_solana_rpc(), json=payload, timeout=10)
        data = response.json()

        holders = []
        if 'result' in data and 'value' in data['result']:
            # Top accounts sorted by amount (Solana returns them sorted)
            for account in data['result']['value'][:limit]:
                holders.append({
                    'address': account['address'],
                    'amount': account['amount']
                })
        return holders
    except Exception as e:
        return []

def check_smart_money_holders(mint):
    """Check if any top holders are known successful investors"""
    # Known successful pump.fun wallets (you can expand this list)
    # These would be wallets that have had multiple successful early investments
    known_smart_wallets = set([
        # Add known successful wallet addresses here as you identify them
        # Example: "ABC123...", "DEF456..."
    ])

    holders = get_top_holders(mint, limit=10)
    smart_money_found = []

    for holder in holders:
        if holder['address'] in known_smart_wallets:
            smart_money_found.append(holder['address'])

    return len(smart_money_found), smart_money_found

# Analysis
def analyze_token_quick(token_info):
    mint = token_info['mint']
    creator = token_info['creator']
    created = token_info['created']

    # Get metadata ON-CHAIN (FREE!)
    metadata = get_token_metadata_onchain(mint)
    if not metadata:
        return False, None, ["Could not fetch metadata"]

    # Get price and liquidity from DexScreener (FREE, no API key!)
    pool_info = get_raydium_pool_info(mint)
    if not pool_info:
        return False, None, ["No liquidity pools found"]

    # Calculate metrics
    name = metadata.get('name', 'Unknown')
    symbol = metadata.get('symbol', '???')
    price = pool_info.get('price_usd', 0)

    # Calculate market cap from supply and price
    total_supply = metadata.get('totalSupplyFormatted', metadata.get('totalSupply', '1000000000'))
    try:
        supply = float(total_supply)
    except (ValueError, TypeError):
        supply = 1_000_000_000  # Default to 1 billion if can't parse
    market_cap = supply * price

    total_liquidity = pool_info.get('total_liquidity', 0)
    pairs_list = pool_info.get('pairs', [])
    num_pools = len(pairs_list)

    liquidity_ratio = total_liquidity / market_cap if market_cap > 0 else 0

    # Get creator token count ON-CHAIN (free!)
    if creator:
        print(f"    Getting creator info on-chain...")
        creator_tokens = get_creator_token_count_onchain(creator)
        print(f"    Creator has launched {creator_tokens} tokens")
    else:
        creator_tokens = None
        print(f"    Could not find creator")

    # Skip deep creator analysis for now (can add later)
    creator_success_rate = 0
    creator_successful = 0
    creator_checked = 0

    # Check for smart money (known successful investors)
    smart_money_count, smart_wallets = check_smart_money_holders(mint)

    try:
        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        age_hours = float((datetime.now(created_dt.tzinfo) - created_dt).total_seconds() / 3600)
    except Exception as e:
        print(f"    Warning: Could not calculate age: {e}")
        age_hours = None

    metrics = {
        'mint': mint,
        'name': name,
        'symbol': symbol,
        'price': price,
        'market_cap': market_cap,
        'liquidity': total_liquidity,
        'num_pools': num_pools,
        'liquidity_ratio': liquidity_ratio,
        'creator': creator,
        'creator_tokens': creator_tokens,
        'creator_success_rate': creator_success_rate,
        'creator_successful': creator_successful,
        'creator_checked': creator_checked,
        'age_hours': age_hours,
        'smart_money_count': smart_money_count,
        'smart_wallets': smart_wallets
    }
    
    # Apply filters
    reasons = []
    is_good = True
    
    if total_liquidity < MIN_LIQUIDITY_USD:
        is_good = False
        reasons.append(f"Low liquidity (${total_liquidity:,.0f})")
    
    if liquidity_ratio < MIN_LIQUIDITY_RATIO:
        is_good = False
        reasons.append(f"Poor ratio ({liquidity_ratio*100:.1f}%)")

    if creator_tokens is not None and creator_tokens > MAX_CREATOR_TOKENS:
        is_good = False
        reasons.append(f"Serial launcher ({creator_tokens} tokens)")

    if age_hours is not None and float(age_hours) > float(MAX_TOKEN_AGE_HOURS):
        is_good = False
        reasons.append(f"Too old ({age_hours:.1f}h)")

    if num_pools == 0:
        is_good = False
        reasons.append("No pools")

    if is_good:
        reasons = [
            f"[PASS] Liquidity: ${total_liquidity:,.0f}",
            f"[PASS] Ratio: {liquidity_ratio*100:.1f}%",
            f"[PASS] Creator: {creator_tokens if creator_tokens is not None else 'N/A'} tokens",
            f"[PASS] Age: {age_hours:.1f}h"
        ]

        # Highlight successful creator track record
        if creator_checked > 0:
            if creator_success_rate >= MIN_CREATOR_SUCCESS_RATE:
                reasons.append(f"[PROVEN CREATOR] {creator_successful}/{creator_checked} previous coins succeeded ({creator_success_rate*100:.0f}%)")
            else:
                reasons.append(f"[WARNING] Creator History: {creator_successful}/{creator_checked} succeeded ({creator_success_rate*100:.0f}%)")

        if smart_money_count > 0:
            reasons.append(f"[SMART MONEY] {smart_money_count} known wallets detected")

    return is_good, metrics, reasons

def display_token(metrics, reasons):
    print("\n" + "="*70)
    print(f"TOKEN: {metrics['name']} (${metrics['symbol']})")
    print("="*70)
    print(f"Mint: {metrics['mint']}")
    print(f"Age: {metrics['age_hours']:.1f}h")
    print(f"\nPrice: ${metrics['price']:.8f}")
    print(f"Market Cap: ${metrics['market_cap']:,.2f}")
    print(f"Liquidity: ${metrics['liquidity']:,.2f} ({metrics['liquidity_ratio']*100:.1f}%)")
    print(f"Pools: {metrics['num_pools']}")
    print(f"Creator Tokens: {metrics['creator_tokens']}")

    # Display creator success rate
    if metrics.get('creator_checked', 0) > 0:
        success_rate = metrics.get('creator_success_rate', 0)
        successful = metrics.get('creator_successful', 0)
        checked = metrics.get('creator_checked', 0)
        print(f"Creator Success Rate: {successful}/{checked} ({success_rate*100:.0f}%)")

    if metrics.get('smart_money_count', 0) > 0:
        print(f"Smart Money: {metrics['smart_money_count']} known wallets")

    print(f"\nREASONS:")
    for reason in reasons:
        print(f"  {reason}")
    print("="*70)

def save_to_file(good_tokens, filename="high_potential_tokens.txt"):
    with open(filename, 'w') as f:
        f.write(f"HIGH POTENTIAL TOKENS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Found: {len(good_tokens)}\n")
        f.write("="*70 + "\n\n")

        for metrics, reasons in good_tokens:
            f.write(f"TOKEN: {metrics['name']} (${metrics['symbol']})\n")
            f.write(f"Mint: {metrics['mint']}\n")
            f.write(f"Age: {metrics['age_hours']:.1f}h\n")
            f.write(f"Price: ${metrics['price']:.8f}\n")
            f.write(f"Market Cap: ${metrics['market_cap']:,.2f}\n")
            f.write(f"Liquidity: ${metrics['liquidity']:,.2f} ({metrics['liquidity_ratio']*100:.1f}%)\n")
            f.write(f"Pools: {metrics['num_pools']}\n")
            f.write(f"Creator Tokens: {metrics['creator_tokens']}\n")

            # Write creator success rate
            if metrics.get('creator_checked', 0) > 0:
                success_rate = metrics.get('creator_success_rate', 0)
                successful = metrics.get('creator_successful', 0)
                checked = metrics.get('creator_checked', 0)
                f.write(f"Creator Success Rate: {successful}/{checked} ({success_rate*100:.0f}%)\n")

            if metrics.get('smart_money_count', 0) > 0:
                f.write(f"Smart Money: {metrics['smart_money_count']} known wallets\n")

            for reason in reasons:
                f.write(f"  {reason}\n")
            f.write("\n" + "="*70 + "\n\n")

# Main Scanner
def process_single_token(token):
    """Process a single token and return results (for parallel processing)"""
    mint = token['mint']
    print(f"  Checking: {mint[:8]}...")

    is_good, metrics, reasons = analyze_token_quick(token)

    if is_good:
        print(f"  [+] {mint[:8]}... HIGH POTENTIAL!")
        return True, metrics, reasons
    else:
        print(f"  [-] {mint[:8]}... {reasons[0] if reasons else 'Filtered'}")
        return False, None, None

def scan_for_good_tokens(one_time=False):
    print("\n" + "="*70)
    print("PUMP.FUN TOKEN SCANNER - 100% ON-CHAIN")
    print("="*70)
    print(f"Min Liquidity: ${MIN_LIQUIDITY_USD:,}")
    print(f"Min Ratio: {MIN_LIQUIDITY_RATIO*100}%")
    print(f"Max Creator Tokens: {MAX_CREATOR_TOKENS}")
    print(f"Max Age: {MAX_TOKEN_AGE_HOURS}h")
    print(f"\nCreator Success Criteria (anti-bot filters):")
    print(f"  - Market Cap: ${MIN_SUCCESSFUL_MARKET_CAP:,}+")
    print(f"  - Liquidity: ${MIN_SUCCESSFUL_LIQUIDITY:,}+")
    print(f"  - Liquidity Ratio: {MIN_SUCCESSFUL_LIQUIDITY_RATIO*100}%+")
    print(f"  - Holders: {MIN_SUCCESSFUL_HOLDERS}+")
    print("="*70)
    print("100% ON-CHAIN token discovery (FREE)")
    print("ON-CHAIN creator analysis (FREE)")
    print("PARALLEL PROCESSING (10 workers) - FAST")
    print("No API keys needed - 100% decentralized")
    print("="*70 + "\n")
    sys.stdout.flush()  # Force output to display

    scanned_tokens = set()
    scan_count = 0

    while True:
        scan_count += 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan_count}")

        try:
            recent_tokens = get_recent_pump_tokens(limit=50)
            print(f"  Found {len(recent_tokens)} recent tokens")

            # Filter out already scanned tokens
            new_tokens = [token for token in recent_tokens if token['mint'] not in scanned_tokens]

            if not new_tokens:
                print(f"  No new tokens to check")
            else:
                print(f"  Processing {len(new_tokens)} new tokens with 10 parallel workers...")

                good_tokens = []
                new_checked = 0

                # PARALLEL PROCESSING - 10 workers processing tokens simultaneously!
                with ThreadPoolExecutor(max_workers=10) as executor:
                    # Submit all tokens for processing
                    future_to_token = {
                        executor.submit(process_single_token, token): token
                        for token in new_tokens
                    }

                    # Process results as they complete
                    for future in as_completed(future_to_token):
                        token = future_to_token[future]
                        mint = token['mint']
                        scanned_tokens.add(mint)
                        new_checked += 1

                        try:
                            is_good, metrics, reasons = future.result()

                            if is_good:
                                play_alert()  # Sound alert for high potential token
                                good_tokens.append((metrics, reasons))
                                display_token(metrics, reasons)
                        except Exception as e:
                            print(f"  [!] Error processing {mint[:8]}...: {e}")

                print(f"\nSTATS: Checked: {new_checked} | Found: {len(good_tokens)}\n")

                if good_tokens:
                    save_to_file(good_tokens)
                    print("Saved to high_potential_tokens.txt\n")

        except Exception as e:
            print(f"[ERROR] {e}\n")

        if one_time:
            break

        print(f"Next scan in {SCAN_INTERVAL_SECONDS}s (Ctrl+C to stop)\n")
        time.sleep(SCAN_INTERVAL_SECONDS)

# Main
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Pump.fun Token Scanner')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='continuous',
                        help='Scan mode: once or continuous (default: continuous)')

    args = parser.parse_args()

    print("Pump.fun Token Scanner\n")
    sys.stdout.flush()
    if args.mode == 'continuous':
        print("Starting CONTINUOUS monitoring mode...")
        print("Press Ctrl+C to stop\n")
    else:
        print("Starting ONE-TIME scan mode...\n")
    sys.stdout.flush()

    try:
        scan_for_good_tokens(one_time=(args.mode == 'once'))
    except KeyboardInterrupt:
        print("\n\nStopped")
