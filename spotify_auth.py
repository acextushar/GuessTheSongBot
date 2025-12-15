import json
import requests
import time

# --- CONSTANTS (UPDATE THESE IN config.json) ---
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"

class SpotifyAuthenticator:
    """
    Handles Spotify OAuth flow: getting initial tokens, refreshing expired tokens, 
    and persisting them to config.json.
    """
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        self.client_id = self.config.get("SPOTIFY_CLIENT_ID")
        self.client_secret = self.config.get("SPOTIFY_CLIENT_SECRET")
        self.access_token = self.config.get("SPOTIFY_ACCESS_TOKEN")
        self.refresh_token = self.config.get("SPOTIFY_REFRESH_TOKEN")
        self.token_expiry = self.config.get("SPOTIFY_TOKEN_EXPIRY", 0)

        if not self.client_id or not self.client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in config.json.")

    def _save_tokens(self, data):
        """Internal helper to save new tokens and expiry time to config.json."""
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token", self.refresh_token) # Refresh token only returned on initial auth
        
        # Calculate new expiry time (current time + expires_in seconds)
        expires_in = data.get("expires_in", 3600)
        self.token_expiry = int(time.time()) + expires_in
        
        # Update config dictionary
        self.config["SPOTIFY_ACCESS_TOKEN"] = self.access_token
        self.config["SPOTIFY_REFRESH_TOKEN"] = self.refresh_token
        self.config["SPOTIFY_TOKEN_EXPIRY"] = self.token_expiry
        
        # Write back to file
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def is_token_expired(self):
        """Checks if the access token is close to expiry (e.g., within 5 minutes)."""
        return self.token_expiry - time.time() < 300 # Refresh if less than 5 minutes left

    def refresh_token_if_needed(self):
        """
        Refreshes the token if it is expired or close to expiring.
        This is the core logic for Issue #22.
        """
        if self.is_token_expired() or not self.access_token:
            print("--- Refreshing Spotify Token ---")
            if not self.refresh_token:
                raise Exception("Refresh token is missing. Initial authorization required.")
            
            # Request new token using the refresh token
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            try:
                response = requests.post(SPOTIFY_AUTH_URL, data=payload)
                response.raise_for_status()
                data = response.json()
                self._save_tokens(data)
                print("--- Spotify Token Refreshed Successfully ---")
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Could not refresh Spotify token: {e}")
                raise

        return self.access_token

# --- TOKEN RETRY WRAPPER (To be used around API calls) ---

# This function demonstrates how to wrap an API call to handle a 401 error,
# which is the central requirement of Issue #22.
def token_retry_wrapper(auth_handler: SpotifyAuthenticator, api_func, *args, **kwargs):
    """
    Wrapper to execute an API function, checking for a 401 error 
    and retrying after refreshing the token.
    """
    
    # 1. Try to refresh token if needed before the first call
    auth_handler.refresh_token_if_needed()
    
    try:
        # 2. Execute the actual API call
        return api_func(auth_handler.access_token, *args, **kwargs)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("--- API Call failed with 401 Unauthorized. Attempting refresh and retry. ---")
            
            # 3. Force refresh the token (in case the expiry check was slightly off)
            auth_handler.refresh_token_if_needed()
            
            # 4. Retry the API call with the new token
            return api_func(auth_handler.access_token, *args, **kwargs)
        else:
            # Re-raise for other HTTP errors (404, 500, etc.)
            raise