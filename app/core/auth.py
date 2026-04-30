PERMISSIONS_BY_PROFILE = {
    "ADMINISTRADOR": {"dashboard", "obras", "pedidos", "itens", "fornecedores", "locacoes", "orcamentos", "relatorios", "auditoria", "configuracoes"},
    "COMPRADOR": {"dashboard", "obras", "pedidos", "itens", "fornecedores", "relatorios"},
    "PATRAO": {"dashboard", "obras", "pedidos", "itens", "fornecedores", "locacoes", "orcamentos", "relatorios", "auditoria"},
    "FINANCEIRO": {"dashboard", "obras", "fornecedores", "orcamentos", "relatorios", "auditoria"},
    "ALMOXARIFADO": {"dashboard", "obras", "pedidos", "itens"},
}


def can_access(profile, module_key):
    allowed = PERMISSIONS_BY_PROFILE.get((profile or "").upper(), set())
    return module_key in allowed
