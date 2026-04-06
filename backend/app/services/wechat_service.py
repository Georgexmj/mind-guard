from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid
import hashlib

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import WechatBinding

_TOKEN_CACHE: dict[str, Any] = {"token": None, "expires_at": None}


def _use_mock_mode() -> bool:
    return bool(settings.WECHAT_MOCK_MODE) or not (
        settings.WECHAT_MP_APPID
        and settings.WECHAT_MP_SECRET
    )


def _get_access_token() -> str:
    if _use_mock_mode():
        return "mock-token"

    now = datetime.utcnow()
    token = _TOKEN_CACHE.get("token")
    expires_at = _TOKEN_CACHE.get("expires_at")
    if token and isinstance(expires_at, datetime) and expires_at > now + timedelta(minutes=3):
        return str(token)

    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": settings.WECHAT_MP_APPID,
        "secret": settings.WECHAT_MP_SECRET,
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()

    if payload.get("errcode"):
        raise RuntimeError(f"WeChat token error: {payload}")

    token = payload.get("access_token")
    expires_in = int(payload.get("expires_in", 7200))
    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expires_at"] = now + timedelta(seconds=max(expires_in - 60, 60))
    return str(token)


def exchange_code_for_openid(code: str) -> Dict[str, Optional[str]]:
    """
    Exchange mini-program login code for openid/unionid.
    Returns mock openid when mock mode is enabled.
    """
    clean_code = (code or "").strip()
    if not clean_code:
        raise ValueError("code is required")

    if _use_mock_mode():
        digest = hashlib.sha1(clean_code.encode("utf-8")).hexdigest()[:24]
        return {
            "openid": f"mock_{digest}",
            "unionid": None,
            "session_key": "mock-session-key",
            "mode": "mock",
        }

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_MP_APPID,
        "secret": settings.WECHAT_MP_SECRET,
        "js_code": clean_code,
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()

    if payload.get("errcode"):
        raise RuntimeError(f"WeChat jscode2session error: {payload}")

    openid = payload.get("openid")
    if not openid:
        raise RuntimeError(f"WeChat jscode2session missing openid: {payload}")

    return {
        "openid": str(openid),
        "unionid": payload.get("unionid"),
        "session_key": payload.get("session_key"),
        "mode": "live",
    }


def send_subscribe_message(
    *,
    openid: str,
    template_id: str,
    data: Dict[str, Dict[str, str]],
    page: Optional[str] = None,
    miniprogram_state: str = "formal",
) -> Dict[str, Any]:
    request_id = str(uuid.uuid4())
    if not openid:
        return {"ok": False, "request_id": request_id, "mode": "skip", "reason": "missing_openid"}
    if not template_id and _use_mock_mode():
        template_id = "mock-template-id"
    if not template_id:
        return {"ok": False, "request_id": request_id, "mode": "skip", "reason": "missing_template_id"}

    if _use_mock_mode():
        return {
            "ok": True,
            "request_id": request_id,
            "mode": "mock",
            "to": openid,
            "template_id": template_id,
            "page": page or settings.WECHAT_MINIPROGRAM_PAGE,
            "data": data,
        }

    token = _get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "page": page or settings.WECHAT_MINIPROGRAM_PAGE,
        "data": data,
        "miniprogram_state": miniprogram_state,
        "lang": "zh_CN",
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        body = resp.json()

    ok = int(body.get("errcode", 0)) == 0
    return {
        "ok": ok,
        "request_id": request_id,
        "mode": "live",
        "response": body,
    }


def send_to_user_by_binding(
    db: Session,
    *,
    user_id: int,
    template_id: str,
    data: Dict[str, Dict[str, str]],
    page: Optional[str] = None,
) -> Dict[str, Any]:
    binding = (
        db.query(WechatBinding)
        .filter(WechatBinding.user_id == user_id, WechatBinding.is_active == True)
        .first()
    )
    if binding is None:
        return {"ok": False, "mode": "skip", "reason": "binding_not_found", "user_id": user_id}

    result = send_subscribe_message(
        openid=binding.openid,
        template_id=template_id,
        data=data,
        page=page,
    )
    if result.get("ok"):
        binding.last_sent_at = datetime.utcnow()
        db.flush()
    result["user_id"] = user_id
    result["binding_id"] = binding.id
    return result
