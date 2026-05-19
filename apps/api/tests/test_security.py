import pytest

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    h = hash_password("hunter2-strong")
    assert h != "hunter2-strong"
    assert verify_password("hunter2-strong", h) is True
    assert verify_password("wrong", h) is False


def test_password_verify_with_garbage_hash():
    assert verify_password("anything", "not-a-real-hash") is False


def test_access_token_roundtrip():
    tok = create_access_token("user-123")
    payload = decode_token(tok, TokenType.ACCESS)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    tok = create_refresh_token("user-456")
    payload = decode_token(tok, TokenType.REFRESH)
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


def test_token_type_mismatch_rejected():
    access = create_access_token("u")
    with pytest.raises(ValueError):
        decode_token(access, TokenType.REFRESH)


def test_invalid_token_rejected():
    with pytest.raises(ValueError):
        decode_token("not.a.jwt", TokenType.ACCESS)
