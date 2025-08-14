"""
Slack API クライアント - slack-activity-reportsから移植した共通機能
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime


class SlackClient:
    """Slack API操作の共通クライアント"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.api_call_count = 0
        self.rate_limit_hits = 0
        
    def make_api_request(self, url: str, method: str = "GET", params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
        """API リクエストを実行し、レート制限を監視する"""
        self.api_call_count += 1
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            else:
                response = requests.post(url, headers=self.headers, json=json_data)
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                if data.get("error") == "rate_limited":
                    self.rate_limit_hits += 1
                    retry_after = int(response.headers.get("Retry-After", 60))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    return self.make_api_request(url, method, params, json_data)
                else:
                    raise Exception(f"Slack API error: {data.get('error')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def get_channel_history(self, channel_id: str, oldest: Optional[str] = None, latest: Optional[str] = None) -> List[Dict]:
        """チャンネルの履歴を取得"""
        url = f"{self.base_url}/conversations.history"
        params = {"channel": channel_id}
        
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest
            
        response = self.make_api_request(url, params=params)
        return response.get("messages", [])
    
    def post_message(self, channel: str, text: str, thread_ts: Optional[str] = None) -> Dict:
        """メッセージを投稿"""
        url = f"{self.base_url}/chat.postMessage"
        data = {
            "channel": channel,
            "text": text
        }
        
        if thread_ts:
            data["thread_ts"] = thread_ts
            
        return self.make_api_request(url, method="POST", json_data=data)
    
    def delete_message(self, channel: str, ts: str) -> Dict:
        """メッセージを削除"""
        url = f"{self.base_url}/chat.delete"
        data = {
            "channel": channel,
            "ts": ts
        }
        
        return self.make_api_request(url, method="POST", json_data=data)
    
    def get_user_info(self, user_id: str) -> Dict:
        """ユーザー情報を取得"""
        url = f"{self.base_url}/users.info"
        params = {"user": user_id}
        
        response = self.make_api_request(url, params=params)
        return response.get("user", {})
    
    def get_channel_info(self, channel_id: str) -> Dict:
        """チャンネル情報を取得"""
        url = f"{self.base_url}/conversations.info"
        params = {"channel": channel_id}
        
        response = self.make_api_request(url, params=params)
        return response.get("channel", {})
