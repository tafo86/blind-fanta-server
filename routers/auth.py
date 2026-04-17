import os
from fastapi import Query
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 1. Setup your Auth0 variables
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ISSUER = f"https://{AUTH0_DOMAIN}/"
JWKS_URL = f"{ISSUER}.well-known/jwks.json"

# 2. Initialize the tools
security = HTTPBearer()
jwks_client = PyJWKClient(JWKS_URL)



def decode_and_validate_jwt(token: str):
    """The heavy lifting: takes a raw token string and verifies it."""
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=API_AUDIENCE,
            issuer=ISSUER
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    
# 3. The Verifier Dependency
def verify_auth0_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Looks for the token in the 'Authorization: Bearer' Header"""
    # Grab the string from the header, pass it to the brain
    return decode_and_validate_jwt(credentials.credentials)
    

def verify_ws_token(token: str = Query(...)):
    """Looks for the token in the '?token=' URL Query"""
    # Grab the string from the URL, pass it to the brain
    return decode_and_validate_jwt(token)

    
def verify_admin_role(user: dict = Depends(verify_auth0_token)):
    # 1. Safely extract the roles using the exact namespace from your Auth0 Action
    # (Defaults to an empty list if the user has no roles)
    user_roles = user.get("https://blind-fanta/roles", [])
    
    # 2. Check if they have the admin role (Check your exact capitalization!)
    if "admin" in user_roles:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have admin grant")