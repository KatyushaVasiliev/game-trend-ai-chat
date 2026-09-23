"""Firestore repository with a local in-memory fallback for first-run demos."""
import json
import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from firebase_admin import credentials, firestore, get_app, initialize_app


class Store:
    def __init__(self):
        self.db = None
        self.data_memory: dict[str, dict] = {}
        self.conversations_memory: dict[str, dict] = {}
        self._connect_firestore()
        self._seed_if_empty()

    def _connect_firestore(self):
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        if not raw:
            return
        try:
            info = json.loads(raw) if raw.startswith("{") else None
            cred = credentials.Certificate(info if info else raw)
            try:
                get_app()
            except ValueError:
                initialize_app(cred)
            self.db = firestore.client()
        except Exception as exc:
            print(f"Firestore unavailable; running in demo memory mode: {exc}")

    @property
    def mode(self):
        return "firestore" if self.db else "demo-memory"

    def _seed_if_empty(self):
        if self.list_data():
            return
        # 120 monthly-like game interest points: sufficient for summary/trend analysis.
        start = date(2016, 1, 1)
        for i in range(120):
            value = 820 + i * 5 + ((i * 37) % 170) - (60 if i % 12 in (5, 6) else 0)
            self.create_data({"date": (start + timedelta(days=30 * i)).isoformat(), "value": value, "memo": f"인디 게임 관심도 관측 #{i + 1}"})

    def _clean(self, doc_id, value):
        result = {"id": doc_id, **value}
        for key in ("created_at", "updated_at"):
            if isinstance(result.get(key), datetime):
                result[key] = result[key].isoformat()
        return result

    def create_data(self, payload):
        payload = dict(payload)
        doc_id = str(uuid4())
        if self.db:
            self.db.collection("data").document(doc_id).set(payload)
        else:
            self.data_memory[doc_id] = payload
        return self._clean(doc_id, payload)

    def list_data(self):
        if self.db:
            rows = [self._clean(doc.id, doc.to_dict()) for doc in self.db.collection("data").stream()]
        else:
            rows = [self._clean(k, v) for k, v in self.data_memory.items()]
        return sorted(rows, key=lambda item: item["date"])

    def update_data(self, doc_id, payload):
        if self.db:
            ref = self.db.collection("data").document(doc_id)
            if not ref.get().exists: return None
            ref.set(dict(payload))
        elif doc_id in self.data_memory:
            self.data_memory[doc_id] = dict(payload)
        else:
            return None
        return self._clean(doc_id, dict(payload))

    def delete_data(self, doc_id):
        if self.db:
            ref = self.db.collection("data").document(doc_id)
            if not ref.get().exists: return False
            ref.delete()
        elif doc_id in self.data_memory:
            del self.data_memory[doc_id]
        else:
            return False
        return True

    def save_conversation(self, payload, doc_id=None):
        now = datetime.now(timezone.utc).isoformat()
        doc_id = doc_id or str(uuid4())
        existing = self.get_conversation(doc_id)
        record = {**payload, "created_at": (existing or {}).get("created_at", now), "updated_at": now}
        if self.db: self.db.collection("conversations").document(doc_id).set(record)
        else: self.conversations_memory[doc_id] = record
        return self._clean(doc_id, record)

    def list_conversations(self):
        if self.db: rows = [self._clean(d.id, d.to_dict()) for d in self.db.collection("conversations").stream()]
        else: rows = [self._clean(k, v) for k, v in self.conversations_memory.items()]
        return sorted(rows, key=lambda x: x.get("updated_at", ""), reverse=True)

    def get_conversation(self, doc_id):
        if self.db:
            doc = self.db.collection("conversations").document(doc_id).get()
            return self._clean(doc.id, doc.to_dict()) if doc.exists else None
        row = self.conversations_memory.get(doc_id)
        return self._clean(doc_id, row) if row else None

    def delete_conversation(self, doc_id):
        if not self.get_conversation(doc_id): return False
        if self.db: self.db.collection("conversations").document(doc_id).delete()
        else: del self.conversations_memory[doc_id]
        return True


store = Store()
