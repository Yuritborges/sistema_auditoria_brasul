# Build remoto do Sistema de Auditoria

Este fluxo permite gerar o executavel da auditoria no GitHub (sem depender da maquina do escritorio) e publicar na rede via VPN/AnyDesk.

## 1) Rodar build no GitHub

1. Abra o repositorio `sistema_auditoria_brasul` no GitHub.
2. Entre em **Actions**.
3. Execute o workflow **Build Sistema Auditoria** usando **Run workflow** na branch `main`.
4. Aguarde a conclusao (job `build`).
5. Baixe o artefato `SistemaAuditoriaBrasul-<sha>`.

> Se uma execucao antiga falhou, prefira **Run workflow** em vez de **Re-run** para usar o codigo mais recente.

## 2) Publicar na rede

1. Extraia o zip baixado em uma pasta local (ex.: `C:\Temp\SISTEMA AUDITORIA BRASUL`).
2. No projeto da rede (`Z:\0 OBRAS\sistema_auditoria_brasul`), rode:

```powershell
powershell -ExecutionPolicy Bypass -File tools\publicar_build_na_rede.ps1 -Origem "C:\Temp\SISTEMA AUDITORIA BRASUL"
```

O script:
- cria um snapshot em `releases\SistemaAuditoriaBrasul_YYYYMMDD_HHmm`
- atualiza a pasta `current\` usada pelos atalhos

## 3) Validacao rapida

- abrir `current\SISTEMA AUDITORIA BRASUL.exe`
- conferir carregamento dos dados de pedidos (`cotacao_rede.db`)
- validar ao menos uma tela de pendencias e um filtro
