import tempfile

from app.core.audit_store import AuditStore


def test_password_hashing_pbkdf2_and_legacy_compat():
    with tempfile.TemporaryDirectory() as tmp:
        store = AuditStore(tmp)
        store.upsert_user("JOAO", "ADMIN", True, senha="1234")
        assert store.verify_user_password("JOAO", "1234") is True
        assert store.verify_user_password("JOAO", "xxxx") is False

        # Simula hash legado SHA256 para validar compatibilidade.
        import hashlib

        legacy = hashlib.sha256("abcd".encode("utf-8")).hexdigest()
        conn = store._connect()
        try:
            conn.execute("UPDATE usuarios SET senha_hash=? WHERE nome='JOAO'", (legacy,))
            conn.commit()
        finally:
            conn.close()
        assert store.verify_user_password("JOAO", "abcd") is True
