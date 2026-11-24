"""Recipient-owned writer secrets and their MongoDB enrollment records."""
from __future__ import annotations

import hashlib
import re

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from .models import Conflict


def bearer_id(header: bytes) -> str | None:
    if not re.fullmatch(rb"Bearer rlw1\.[a-zA-Z0-9_-]{43}", header):
        return None
    return hashlib.sha256(header[7:]).hexdigest()


def _check_id(value):
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{64}", value):
        raise ValueError("Invalid writer credential identifier")


def _view(row):
    return {"name": row["name"], "credential_id": row["_id"], "expires_at": row["expires_at"],
            "revoked": row["revoked"]}


class WriterRegistry:
    def __init__(self, store):
        self.rows = store.database[store.prefix + "writer_credentials"]
        self.clock = store.clock

    def grant(self, name, credential_id, valid_days=7, *, actor):
        _check_id(credential_id)
        if not isinstance(name, str) or not re.fullmatch("[a-z][a-z0-9_-]{0,63}", name):
            raise ValueError("Invalid writer name")
        if type(valid_days) is not int or not 1 <= valid_days <= 90:
            raise ValueError("Writer validity must be 1 to 90 days")
        # An identity has at most one outstanding credential. Retain revoked IDs
        # so a delayed grant retry cannot reactivate a former bearer's access.
        self.rows.create_index("name", unique=True, partialFilterExpression={"revoked": False},
                               name="outstanding_writer_name")
        now = self.clock()
        # Free only a name that already cannot authenticate. The unique index
        # arbitrates competing replacements; its former fingerprint remains spent.
        self.rows.update_one({"name": name, "revoked": False, "expires_at": {"$lte": now}},
                             {"$set": {"revoked": True, "retired_at": now,
                                       "retirement_reason": "expired"}})
        row = {"_id": credential_id, "name": name, "granted_by": actor, "granted_at": now,
               "valid_days": valid_days, "expires_at": now + valid_days * 86400, "revoked": False}
        try:
            self.rows.insert_one(row)
        except DuplicateKeyError:
            existing = self.rows.find_one({"_id": credential_id, "name": name,
                                           "valid_days": valid_days, "revoked": False,
                                           "expires_at": {"$gt": now}})
            if existing is None:
                raise Conflict("Writer name or credential is already enrolled") from None
            row = existing
        return _view(row)

    def revoke(self, credential_id, *, actor):
        _check_id(credential_id)
        row = self.rows.find_one_and_update({"_id": credential_id, "revoked": False},
            {"$set": {"revoked": True, "revoked_at": self.clock(), "revoked_by": actor}},
            return_document=ReturnDocument.AFTER)
        if row is None:
            row = self.rows.find_one({"_id": credential_id})
            if row is None:
                raise KeyError("Unknown writer credential")
        return _view(row)

    def authenticate(self, credential_id):
        row = self.rows.find_one({"_id": credential_id, "revoked": False,
                                  "expires_at": {"$gt": self.clock()}}, {"name": 1})
        return "mcp-writer:" + row["name"] if row else None
