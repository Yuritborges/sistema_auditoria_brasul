# Build remoto do Sistema de Auditoria

Este fluxo permite gerar o executavel da auditoria no GitHub (sem depender da maquina do escritorio) e publicar na rede via VPN/AnyDesk.

## 1) Release oficial — tag de versao (recomendado)

Depois de **commit + push** em `main`:

```powershell
powershell -ExecutionPolicy Bypass -File tools\tag_release.ps1 -Versao 1.0.1
```

Isso dispara o build e cria **Releases** no GitHub com o zip `SistemaAuditoriaBrasul-v1.0.1.zip`. Checklist: `docs/CHECKLIST_BUILD_RELEASE.md`.

## 2) Build sem tag (teste rapido)

1. Abra o repositorio `sistema_auditoria_brasul` no GitHub.
2. Entre em **Actions**.
3. Execute o workflow **Build Sistema Auditoria** usando **Run workflow** na branch `main`.
4. Aguarde a conclusao (job `build`).
5. Baixe o artefato `SistemaAuditoriaBrasul-<sha>` (30 dias).

> Se uma execucao antiga falhou, prefira **Run workflow** em vez de **Re-run** para usar o codigo mais recente.

## 3) Publicar na rede

1. Extraia o zip baixado em uma pasta local (ex.: `C:\Temp\SISTEMA AUDITORIA BRASUL`).
2. No projeto da rede (`Z:\0 OBRAS\sistema_auditoria_brasul`), rode:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SISTEMA AUDITORIA BRASUL"
```

O script:
- cria um snapshot em `releases\SistemaAuditoriaBrasul_YYYYMMDD_HHmm`
- atualiza a pasta `current\` usada pelos atalhos

## 4) Validacao rapida

- abrir `current\SISTEMA AUDITORIA BRASUL.exe`
- conferir carregamento dos dados de pedidos (`cotacao_rede.db`)
- validar ao menos uma tela de pendencias e um filtro
