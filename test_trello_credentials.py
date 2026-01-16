#!/usr/bin/env python3
"""
Test script to verify Trello API credentials before using in Home Assistant.

Usage:
    python test_trello_credentials.py YOUR_API_KEY YOUR_TOKEN
"""

import sys

def test_credentials(api_key, token):
    """Test Trello credentials."""
    print("=" * 60)
    print("Trello API Credential Test")
    print("=" * 60)
    print()
    
    # Validate inputs
    print("1. Validating input format...")
    print(f"   API Key length: {len(api_key)} characters")
    print(f"   Token length: {len(token)} characters")
    print(f"   Token starts with: {token[:4]}")
    print()
    
    if len(api_key) != 32:
        print("   ⚠️  WARNING: API key should be 32 characters")
    else:
        print("   ✓ API key length looks good")
        
    if not token.startswith("ATTA"):
        print("   ⚠️  WARNING: Token should start with 'ATTA'")
    else:
        print("   ✓ Token format looks good")
        
    if len(token) < 60:
        print("   ⚠️  WARNING: Token seems short (should be ~64 chars)")
    else:
        print("   ✓ Token length looks good")
    
    print()
    print("2. Testing API connection...")
    
    try:
        import requests
        
        # Test with Trello API directly
        url = f"https://api.trello.com/1/members/me"
        params = {
            "key": api_key,
            "token": token
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✓ Connection successful!")
            print()
            print("3. Account information:")
            print(f"   Username: {data.get('username', 'N/A')}")
            print(f"   Full Name: {data.get('fullName', 'N/A')}")
            print(f"   Email: {data.get('email', 'N/A')}")
            print(f"   Member ID: {data.get('id', 'N/A')}")
            print()
            
            # Test boards access
            boards_url = f"https://api.trello.com/1/members/me/boards"
            boards_response = requests.get(boards_url, params=params, timeout=10)
            
            if boards_response.status_code == 200:
                boards = boards_response.json()
                open_boards = [b for b in boards if not b.get('closed', False)]
                print("4. Boards access:")
                print(f"   ✓ Found {len(open_boards)} open boards")
                if open_boards:
                    print("   Board names:")
                    for board in open_boards[:5]:  # Show first 5
                        print(f"     - {board.get('name', 'Unknown')}")
                    if len(open_boards) > 5:
                        print(f"     ... and {len(open_boards) - 5} more")
            print()
            print("=" * 60)
            print("✓ ALL TESTS PASSED - Credentials are valid!")
            print("=" * 60)
            print()
            print("You can now use these credentials in Home Assistant.")
            return True
            
        elif response.status_code == 401:
            print("   ✗ Authentication failed (401 Unauthorized)")
            print()
            print("Possible issues:")
            print("  - API key is incorrect")
            print("  - Token is incorrect or expired")
            print("  - Token was revoked")
            print()
            print("Try:")
            print("  1. Generate a new token at https://trello.com/app-key")
            print("  2. Copy the ENTIRE token (usually ~64 characters)")
            print("  3. Make sure there are no extra spaces")
            return False
            
        else:
            print(f"   ✗ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except ImportError:
        print("   ℹ️  'requests' library not installed")
        print()
        print("Install it with: pip install requests")
        print()
        print("Or test manually in your browser:")
        print(f"https://api.trello.com/1/members/me?key={api_key}&token={token}")
        return None
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_trello_credentials.py API_KEY TOKEN")
        print()
        print("Example:")
        print("  python test_trello_credentials.py abc123... ATTAdef456...")
        print()
        print("Get your credentials from: https://trello.com/app-key")
        sys.exit(1)
    
    api_key = sys.argv[1].strip()
    token = sys.argv[2].strip()
    
    result = test_credentials(api_key, token)
    
    if result is True:
        sys.exit(0)
    elif result is False:
        sys.exit(1)
    else:
        sys.exit(2)
