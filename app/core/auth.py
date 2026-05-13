PROFILE_ALIASES = {
    "PATRAO": "ADMIN",
    "PATRÃO": "ADMIN",
    "ADMINISTRADOR": "ADMIN",
}

PERMISSIONS_BY_PROFILE = {
    "ADMIN": {
        "dashboard",
        "obras",
        "pedidos",
        "itens",
        "fornecedores",
        "relatorios",
        "auditoria",
        "configuracoes",
        "contratos",
        "medicoes",
        "conciliacao",
        "fiscalizacao",
    },
    "COMPRADOR": {"dashboard", "pedidos", "itens", "fornecedores", "relatorios"},
    "FINANCEIRO": {
        "dashboard",
        "obras",
        "fornecedores",
        "relatorios",
        "auditoria",
        "contratos",
        "medicoes",
        "conciliacao",
        "fiscalizacao",
    },
}


def normalize_profile(profile):
    raw = (profile or "").strip().upper()
    if not raw:
        return "COMPRADOR"
    return PROFILE_ALIASES.get(raw, raw)


def is_admin(profile):
    return normalize_profile(profile) == "ADMIN"


def assignable_profiles(operator_profile, allow_admin=False):
    base = ["COMPRADOR", "FINANCEIRO"]
    if allow_admin or is_admin(operator_profile):
        return ["ADMIN"] + base
    return base


def can_access(profile, module_key):
    allowed = PERMISSIONS_BY_PROFILE.get(normalize_profile(profile), set())
    return module_key in allowed
