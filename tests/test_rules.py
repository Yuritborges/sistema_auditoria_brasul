from app.core.auth import normalize_profile
from app.services.auditoria_service import AuditoriaService


def test_normalize_profile_aliases():
    assert normalize_profile("patrao") == "ADMIN"
    assert normalize_profile("ADMINISTRADOR") == "ADMIN"
    assert normalize_profile("") == "COMPRADOR"


def test_norm_numero_strips_zeros():
    svc = AuditoriaService()
    assert svc._norm_numero("000123") == "123"
    assert svc._norm_numero("001") == "1"
    assert svc._norm_numero("000") == "0"
