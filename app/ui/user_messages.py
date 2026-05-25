"""Textos exibidos ao usuário final (sem caminhos, comandos ou detalhes técnicos)."""


def erro_generico(acao: str = "concluir a operação") -> str:
    return f"Não foi possível {acao}. Tente novamente ou peça ajuda ao suporte."


def erro_salvar(item: str) -> str:
    return erro_generico(f"salvar {item}")


def erro_carregar(item: str = "os dados") -> str:
    return erro_generico(f"carregar {item}")
