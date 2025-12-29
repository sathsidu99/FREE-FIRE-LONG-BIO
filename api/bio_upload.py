import json
import requests
import binascii
import jwt
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib.parse
from http.server import BaseHTTPRequestHandler
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
FREEFIRE_UPDATE_URL = "https://clientbp.ggblueshark.com/UpdateSocialBasicInfo"
MAJOR_LOGIN_URL = "https://loginbp.ggblueshark.com/MajorLogin"
OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
FREEFIRE_VERSION = "OB51"

KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

BIO_HEADERS = {
    "Expect": "100-continue",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": FREEFIRE_VERSION,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}

LOGIN_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/octet-stream",
    "Expect": "100-continue",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": FREEFIRE_VERSION
}

def encrypt_data(data_bytes):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded)

def decode_jwt_info(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        name = decoded.get("nickname")
        region = decoded.get("lock_region") 
        uid = decoded.get("account_id")
        return str(uid), name, region
    except:
        return None, None, None

def perform_guest_login(uid, password):
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;pt;BR;)",
        'Connection': "Keep-Alive"
    }
    try:
        resp = requests.post(OAUTH_URL, data=payload, headers=headers, timeout=10, verify=False)
        data = resp.json()
        if 'access_token' in data:
            return data['access_token'], data.get('open_id')
    except Exception as e:
        print(f"Guest login error: {e}")
    return None, None

def upload_bio_request(jwt_token, bio_text):
    try:
        # For Vercel, we'll simplify the protobuf part
        # This is a simplified version - you may need to adjust
        data_bytes = bio_text.encode()  # Simplified
        encrypted = encrypt_data(data_bytes)

        headers = BIO_HEADERS.copy()
        headers["Authorization"] = f"Bearer {jwt_token}"

        resp = requests.post(FREEFIRE_UPDATE_URL, headers=headers, data=encrypted, timeout=20, verify=False)

        status_text = "Unknown"
        if resp.status_code == 200: 
            status_text = "✅ Success"
        elif resp.status_code == 401: 
            status_text = "❌ Unauthorized (Invalid JWT)"
        else: 
            status_text = f"⚠️ Status {resp.status_code}"

        raw_hex = binascii.hexlify(resp.content).decode('utf-8')

        return {
            "status": status_text,
            "code": resp.status_code,
            "bio": bio_text,
            "server_response": raw_hex[:100] + "..." if len(raw_hex) > 100 else raw_hex
        }
    except Exception as e:
        return {"status": f"Error: {str(e)}", "code": 500, "bio": bio_text, "server_response": "N/A"}

def handler(event, context):
    # Handle CORS preflight
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    # Parse query parameters
    params = event.get('queryStringParameters', {}) or {}
    bio = params.get('bio', '')
    jwt_token = params.get('jwt', '')
    uid = params.get('uid', '')
    password = params.get('pass', '')
    access_token = params.get('access', params.get('access_token', ''))
    
    if not bio:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "status": "❌ Error",
                "code": 400,
                "error": "Missing 'bio' parameter"
            })
        }
    
    # Simplified logic for Vercel
    login_method = "Unknown"
    final_jwt = jwt_token
    
    if not final_jwt and uid and password:
        login_method = "UID/Pass Login"
        acc_token, openid = perform_guest_login(uid, password)
        if acc_token:
            final_jwt = acc_token  # Simplified
    
    if not final_jwt and access_token:
        login_method = "Access Token Login"
        final_jwt = access_token  # Simplified
    
    if not final_jwt:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                "status": "❌ Error",
                "code": 400,
                "error": "No valid authentication provided"
            })
        }
    
    # Upload bio
    result = upload_bio_request(final_jwt, bio)
    
    response_data = {
        "Credit": "Flexbase",
        "Join For More": "Telegram: @Flexbasei",
        "status": result["status"],
        "login_method": login_method or "Direct JWT",
        "code": result["code"],
        "bio": result["bio"],
        "server_response": result["server_response"],
        "note": "This is a simplified Vercel version. For full features, use local Flask app."
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response_data)
    }

# For local testing
if __name__ == "__main__":
    class MockEvent:
        def __init__(self):
            self.httpMethod = "GET"
            self.queryStringParameters = {
                "bio": "Test Bio",
                "jwt": "test.jwt.token"
            }
    
    mock_event = MockEvent()
    mock_context = {}
    result = handler(mock_event, mock_context)
    print(result)
