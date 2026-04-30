import os
from datetime import datetime
import re
import json
import csv
import sqlite3

from app.config import BASE_DIR, resolve_db_path, resolve_pdf_roots, pdf_index_cache_path
from app.core.audit_store import AuditStore
from app.data.auditoria_repository import AuditoriaRepository


class AuditoriaService:
    _pdf_index = None

    def __init__(self):
        self.audit_store = AuditStore(BASE_DIR)

    def carregar(self):
        db_path = resolve_db_path()
        if db_path:
            repo = AuditoriaRepository(db_path)
            dados = repo.listar_pedidos()
            origem = f"Banco real: {db_path}"
        else:
            dados = self._dados_demo()
            origem = "Modo demonstracao: banco consolidado nao encontrado"

        for item in dados:
            self._enriquecer_item(item)
        dados.sort(key=self._chave_ordenacao, reverse=True)
        return dados, origem

    def _enriquecer_item(self, item):
        item["origem"] = (item.get("comprador") or "").strip().upper()
        item["pdf_rede"] = self._resolver_pdf(item)
        item["sem_pdf"] = not (item["pdf_rede"] and os.path.exists(item["pdf_rede"]))
        item["sem_comprador"] = not (item.get("comprador") or "").strip()
        item["status_auditoria"] = self._status_auditoria(item)
        item["itens_lista"] = self._normalizar_itens(item.get("itens_texto") or "")

    def _status_auditoria(self, item):
        if item["sem_pdf"] and item["sem_comprador"]:
            return "Critico"
        if item["sem_pdf"]:
            return "Sem PDF"
        if item["sem_comprador"]:
            return "Sem comprador"
        return "OK"

    def _chave_ordenacao(self, item):
        texto = item.get("data_pedido") or ""
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(texto, fmt)
            except Exception:
                pass
        return datetime.min

    def _normalizar_itens(self, itens_texto):
        itens = []
        for bruto in itens_texto.split("|"):
            txt = re.sub(r"\s+", " ", bruto).strip()
            if txt:
                itens.append(txt)
        return itens

    def _resolver_pdf(self, item):
        caminho = (item.get("caminho_pdf") or "").strip()
        if caminho and os.path.exists(caminho):
            return caminho

        numero = str(item.get("numero") or "").strip()
        if not numero:
            return ""

        if AuditoriaService._pdf_index is None:
            AuditoriaService._pdf_index = self._carregar_indice_cache()

        return AuditoriaService._pdf_index.get(numero, "")

    def buscar_pdfs_filtrados(self, pedidos, filtros):
        faltando = {}
        for item in pedidos:
            if item.get("pdf_rede"):
                continue
            numero = str(item.get("numero") or "").strip()
            if numero:
                faltando[numero] = item

        if not faltando:
            return 0

        tokens = self._tokens_contexto(filtros)
        encontrados = self._varrer_pdfs_contextual(faltando, tokens)
        self._salvar_indice_cache(AuditoriaService._pdf_index or {})

        for item in pedidos:
            item["sem_pdf"] = not (item.get("pdf_rede") and os.path.exists(item.get("pdf_rede")))
            item["status_auditoria"] = self._status_auditoria(item)
        return encontrados

    def _montar_indice_pdf(self):
        indice = {}
        roots = resolve_pdf_roots()
        padrao_numero = re.compile(r"(?<!\d)(\d{3,})(?!\d)")

        for root in roots:
            for dirpath, _, filenames in os.walk(root):
                for filename in filenames:
                    if not filename.lower().endswith(".pdf"):
                        continue
                    caminho = os.path.join(dirpath, filename)
                    base_name = os.path.splitext(filename)[0]
                    for numero in padrao_numero.findall(base_name):
                        # Mantem o primeiro match para o numero.
                        if numero not in indice:
                            indice[numero] = caminho
        return indice

    def _tokens_contexto(self, filtros):
        tokens = []
        for chave in ("comprador", "obra", "fornecedor", "item"):
            valor = (filtros.get(chave) or "").strip().upper()
            if valor and valor not in ("TODOS", "TODAS"):
                tokens.append(valor)
        return tokens

    def _varrer_pdfs_contextual(self, faltando, tokens):
        if AuditoriaService._pdf_index is None:
            AuditoriaService._pdf_index = self._carregar_indice_cache()
        indice = AuditoriaService._pdf_index

        encontrados = 0
        padrao_numero = re.compile(r"(?<!\d)(\d{3,})(?!\d)")
        roots = resolve_pdf_roots()

        numeros_faltando = set(faltando.keys())

        for root in roots:
            if not numeros_faltando:
                break
            root_depth = root.count(os.sep)
            for dirpath, dirnames, filenames in os.walk(root):
                if not numeros_faltando:
                    break

                dir_up = dirpath.upper()
                depth = dirpath.count(os.sep) - root_depth
                if tokens and depth >= 1:
                    dirnames[:] = [d for d in dirnames if any(tok in d.upper() for tok in tokens)]

                for filename in filenames:
                    if not filename.lower().endswith(".pdf"):
                        continue
                    file_up = filename.upper()
                    if tokens and not any(tok in file_up or tok in dir_up for tok in tokens):
                        continue

                    candidatos = padrao_numero.findall(os.path.splitext(filename)[0])
                    if not candidatos:
                        continue
                    inter = [n for n in candidatos if n in numeros_faltando]
                    if not inter:
                        continue

                    caminho = os.path.join(dirpath, filename)
                    for numero in inter:
                        indice[numero] = caminho
                        item = faltando[numero]
                        item["pdf_rede"] = caminho
                        numeros_faltando.discard(numero)
                        encontrados += 1
        return encontrados

    def _carregar_indice_cache(self):
        path = pdf_index_cache_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if isinstance(v, str) and os.path.exists(v)}
        except Exception:
            pass
        return {}

    def _salvar_indice_cache(self, indice):
        path = pdf_index_cache_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(indice, f, ensure_ascii=False)
        except Exception:
            pass

    def _dados_demo(self):
        return [
            {
                "numero": "9001",
                "data_pedido": "14/04/2026",
                "obra_nome": "UBS Vila Maria",
                "fornecedor_nome": "HidraSteel Materiais",
                "empresa_faturadora": "BRASUL",
                "condicao_pagamento": "28",
                "forma_pagamento": "BOLETO",
                "valor_total": 18450.55,
                "caminho_pdf": "",
                "comprador": "IURY",
                "itens_texto": "Tubo galvanizado 2 | Conexao TEE",
            },
            {
                "numero": "9002",
                "data_pedido": "12/04/2026",
                "obra_nome": "EMEF Jardim Helena",
                "fornecedor_nome": "Construforte",
                "empresa_faturadora": "INTERIORANA",
                "condicao_pagamento": "30/60",
                "forma_pagamento": "PIX",
                "valor_total": 9220.0,
                "caminho_pdf": "",
                "comprador": "",
                "itens_texto": "Argamassa AC3 | Rejunte",
            },
            {
                "numero": "9003",
                "data_pedido": "07/04/2026",
                "obra_nome": "Posto de Saude Anhanguera",
                "fornecedor_nome": "Mega Eletrica",
                "empresa_faturadora": "JB",
                "condicao_pagamento": "21",
                "forma_pagamento": "BOLETO",
                "valor_total": 28750.9,
                "caminho_pdf": "",
                "comprador": "THAMYRES",
                "itens_texto": "Quadro de distribuicao | Disjuntor tripolar",
            },
        ]

    # -------- agregacoes para modulos --------
    def dashboard_summary(self, dados):
        hoje = datetime.now()
        total_ano = 0.0
        total_mes = 0.0
        por_empresa = {}
        por_obra = {}
        por_fornecedor = {}
        por_item = {}
        mensal = {m: 0.0 for m in range(1, 13)}
        pendentes = 0
        sem_pdf = 0

        for p in dados:
            valor = float(p.get("valor_total") or 0)
            dt = self._chave_ordenacao(p)
            total_ano += valor if dt.year == hoje.year else 0
            total_mes += valor if (dt.year == hoje.year and dt.month == hoje.month) else 0
            emp = (p.get("empresa_faturadora") or "SEM EMPRESA").strip() or "SEM EMPRESA"
            por_empresa[emp] = por_empresa.get(emp, 0.0) + valor
            obra = (p.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"
            por_obra[obra] = por_obra.get(obra, 0.0) + valor
            forn = (p.get("fornecedor_nome") or "SEM FORNECEDOR").strip() or "SEM FORNECEDOR"
            por_fornecedor[forn] = por_fornecedor.get(forn, 0.0) + valor
            for item in p.get("itens_lista") or []:
                por_item[item] = por_item.get(item, 0) + 1
            if dt.year == hoje.year:
                mensal[dt.month] += valor
            if p.get("status_auditoria") != "OK":
                pendentes += 1
            if p.get("sem_pdf"):
                sem_pdf += 1

        return {
            "total_mes": total_mes,
            "total_ano": total_ano,
            "por_empresa": sorted(por_empresa.items(), key=lambda x: x[1], reverse=True),
            "top_obras": sorted(por_obra.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_fornecedores": sorted(por_fornecedor.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_itens": sorted(por_item.items(), key=lambda x: x[1], reverse=True)[:10],
            "mensal": mensal,
            "pendentes": pendentes,
            "sem_pdf": sem_pdf,
        }

    def obra_details(self, dados, obra_nome):
        alvo = obra_nome.strip().upper()
        pedidos = [p for p in dados if (p.get("obra_nome") or "").strip().upper() == alvo]
        total = sum(float(p.get("valor_total") or 0) for p in pedidos)
        mensal = {m: 0.0 for m in range(1, 13)}
        for p in pedidos:
            dt = self._chave_ordenacao(p)
            mensal[dt.month] += float(p.get("valor_total") or 0)
        return {
            "pedidos": pedidos,
            "valor_total": total,
            "qtd_pedidos": len(pedidos),
            "mensal": mensal,
        }

    def item_auditoria(self, dados, termo):
        t = termo.strip().upper()
        rows = []
        for p in dados:
            valor = float(p.get("valor_total") or 0)
            itens = p.get("itens_lista") or []
            for item in itens:
                if t and t not in item.upper():
                    continue
                rows.append(
                    {
                        "item": item,
                        "obra": p.get("obra_nome") or "SEM OBRA",
                        "fornecedor": p.get("fornecedor_nome") or "SEM FORNECEDOR",
                        "valor": valor,
                        "data": p.get("data_pedido") or "",
                    }
                )
        if not rows:
            return {"rows": [], "stats": {}}
        valores = [r["valor"] for r in rows]
        forn_barato = min(rows, key=lambda x: x["valor"]).get("fornecedor")
        return {
            "rows": rows,
            "stats": {
                "qtd": len(rows),
                "obras": len({r["obra"] for r in rows}),
                "preco_medio": sum(valores) / len(valores),
                "preco_min": min(valores),
                "preco_max": max(valores),
                "fornecedor_mais_barato": forn_barato,
            },
        }

    def fornecedor_auditoria(self, dados, fornecedor):
        alvo = fornecedor.strip().upper()
        rows = [p for p in dados if (p.get("fornecedor_nome") or "").strip().upper() == alvo]
        total = sum(float(p.get("valor_total") or 0) for p in rows)
        return {
            "rows": rows,
            "total": total,
            "qtd_pedidos": len(rows),
            "obras": len({(r.get("obra_nome") or "").strip() for r in rows if (r.get("obra_nome") or "").strip()}),
            "ultima_compra": (rows[0].get("data_pedido") if rows else ""),
        }

    def salvar_orcamento(self, obra, valor_previsto, usuario):
        self.audit_store.upsert_budget(obra, valor_previsto)
        self.audit_store.log("orcamentos_obra", obra, "UPSERT", "valor_previsto", "", valor_previsto, usuario)

    def listar_orcamentos_com_consumo(self, dados):
        gastos = {}
        for p in dados:
            obra = (p.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"
            gastos[obra] = gastos.get(obra, 0.0) + float(p.get("valor_total") or 0)

        obras_base, previstos_base = self._carregar_orcamentos_base_pedidos()
        for obra in obras_base:
            gastos.setdefault(obra, 0.0)

        locais = {o["obra"]: float(o["valor_previsto"] or 0) for o in self.audit_store.list_budgets()}
        todos_orcamentos = dict(previstos_base)
        todos_orcamentos.update(locais)

        out = []
        for obra in sorted(gastos.keys()):
            previsto = float(todos_orcamentos.get(obra, 0) or 0)
            gasto = gastos.get(obra, 0.0)
            consumo = (gasto / previsto * 100) if previsto > 0 else 0
            alerta = "SEM PREVISTO" if previsto <= 0 else "OK"
            if previsto > 0:
                if consumo >= 100:
                    alerta = "CRITICO"
                elif consumo >= 90:
                    alerta = "ALTO"
                elif consumo >= 80:
                    alerta = "ATENCAO"
            out.append(
                {
                    "obra": obra,
                    "previsto": previsto,
                    "gasto": gasto,
                    "saldo": previsto - gasto,
                    "consumo": consumo,
                    "alerta": alerta,
                }
            )
        return out

    def _carregar_orcamentos_base_pedidos(self):
        db_path = self._resolver_db_programa_pedidos()
        if not db_path or not os.path.exists(db_path):
            return [], {}

        obras = set()
        previstos = {}
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            # Obras cadastradas no programa de pedidos.
            try:
                rows_obras = conn.execute("SELECT nome FROM obras").fetchall()
                for r in rows_obras:
                    nome = (r["nome"] or "").strip()
                    if nome:
                        obras.add(nome)
            except Exception:
                pass

            # Obras efetivamente usadas em pedidos.
            try:
                rows_ped = conn.execute("SELECT DISTINCT obra_nome FROM pedidos").fetchall()
                for r in rows_ped:
                    nome = (r["obra_nome"] or "").strip()
                    if nome:
                        obras.add(nome)
            except Exception:
                pass

            # Se existir tabela de orçamento no banco principal no futuro, já suporta.
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if "orcamentos_obra" in tables:
                try:
                    rows_orc = conn.execute("SELECT obra, valor_previsto FROM orcamentos_obra").fetchall()
                    for r in rows_orc:
                        obra = (r["obra"] or "").strip()
                        if obra:
                            previstos[obra] = float(r["valor_previsto"] or 0)
                            obras.add(obra)
                except Exception:
                    pass
        finally:
            conn.close()

        return sorted(obras), previstos

    def _resolver_db_programa_pedidos(self):
        cfg = r"Z:\0 OBRAS\sistema_de_pedidos_brasulv2\config.py"
        if os.path.exists(cfg):
            try:
                with open(cfg, "r", encoding="utf-8") as f:
                    txt = f.read()
                m = re.search(r"DATABASE_PATH\s*=\s*r?\"([^\"]+)\"", txt)
                if m:
                    path = m.group(1)
                    if os.path.exists(path):
                        return path
            except Exception:
                pass
        return resolve_db_path()

    def alertas_automaticos(self, dados):
        alertas = []
        media = (sum(float(p.get("valor_total") or 0) for p in dados) / len(dados)) if dados else 0
        for p in dados:
            numero = p.get("numero") or ""
            valor = float(p.get("valor_total") or 0)
            if p.get("sem_pdf"):
                alertas.append(("Sem PDF", f"Pedido {numero} sem anexo PDF"))
            if not (p.get("fornecedor_nome") or "").strip():
                alertas.append(("Sem fornecedor", f"Pedido {numero} sem fornecedor"))
            if media > 0 and valor > media * 3:
                alertas.append(("Valor alto", f"Pedido {numero} acima de 3x da media"))
        return alertas

    def registrar_auditoria(self, entidade, entidade_id, acao, campo, anterior, novo, usuario):
        self.audit_store.log(entidade, entidade_id, acao, campo, anterior, novo, usuario)

    def listar_logs(self, limit=500):
        return self.audit_store.list_logs(limit=limit)

    def salvar_usuario(self, nome, perfil, ativo, operador):
        self.audit_store.upsert_user(nome, perfil, ativo)
        self.audit_store.log("usuarios", nome, "UPSERT", "perfil", "", perfil, operador)

    def listar_usuarios(self):
        users = self.audit_store.list_users()
        if not users:
            for n, p in [("IURY", "COMPRADOR"), ("THAMYRES", "COMPRADOR"), ("PATRAO", "PATRAO")]:
                self.audit_store.upsert_user(n, p, True)
            users = self.audit_store.list_users()
        return users

    def exportar_csv(self, caminho_arquivo, colunas, linhas):
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        with open(caminho_arquivo, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            for l in linhas:
                writer.writerow({c: l.get(c, "") for c in colunas})
