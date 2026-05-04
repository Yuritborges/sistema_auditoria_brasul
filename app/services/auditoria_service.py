import os
from datetime import datetime
import re
import json
import csv
import sqlite3

from app.config import (
    BASE_DIR,
    OBRAS_JSON_PATH,
    resolve_db_path,
    resolve_pdf_roots,
    pdf_index_cache_path,
)
from app.core.auth import assignable_profiles, is_admin, normalize_profile
from app.core.audit_store import AuditStore
from app.data.auditoria_repository import AuditoriaRepository


class AuditoriaService:
    _pdf_index = None

    def __init__(self):
        self.audit_store = AuditStore(BASE_DIR)
        self._cache_dados = None
        self._cache_origem = ""
        self._pdf_exists_cache = {}
        self._summary_cache = {}
        self._data_version = 0
        self._pdf_full_index_loaded = False

    def carregar(self, force=False):
        if not force and self._cache_dados is not None:
            return [dict(item) for item in self._cache_dados], self._cache_origem
        if force:
            self._pdf_exists_cache = {}
            self._summary_cache = {}

        db_path = resolve_db_path()
        if db_path:
            repo = AuditoriaRepository(db_path)
            dados = repo.listar_pedidos()
            origem = f"Banco real: {db_path}"
        else:
            dados = self._dados_demo()
            origem = "Modo demonstracao: banco consolidado nao encontrado"

        # Evita milhares de os.path.exists na rede durante o primeiro paint — só valida em buscas/abrir PDF.
        self._bulk_pdf_resolve = True
        try:
            for item in dados:
                self._enriquecer_item(item)
        finally:
            self._bulk_pdf_resolve = False
        dados.sort(key=self._chave_ordenacao, reverse=True)
        self._cache_dados = [dict(item) for item in dados]
        self._cache_origem = origem
        self._data_version += 1
        self._summary_cache = {}
        return [dict(item) for item in dados], origem

    def _enriquecer_item(self, item):
        item["_valor_total_float"] = float(item.get("valor_total") or 0)
        item["_data_ord"] = self._parse_data_pedido(item.get("data_pedido") or "")
        item["origem"] = (item.get("comprador") or "").strip().upper()
        item["pdf_rede"] = self._resolver_pdf(item)
        if getattr(self, "_bulk_pdf_resolve", False):
            item["sem_pdf"] = not bool((item.get("pdf_rede") or "").strip())
        else:
            item["sem_pdf"] = not self._pdf_path_exists(item.get("pdf_rede"))
        item["sem_comprador"] = not (item.get("comprador") or "").strip()
        item["status_auditoria"] = self._status_auditoria(item)
        item["itens_lista"] = self._normalizar_itens(item.get("itens_texto") or "")

    def _parse_data_pedido(self, texto):
        txt = texto or ""
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(txt, fmt)
            except Exception:
                pass
        return datetime.min

    def _pdf_path_exists(self, caminho):
        path = (caminho or "").strip()
        if not path:
            return False
        if path in self._pdf_exists_cache:
            return self._pdf_exists_cache[path]
        ok = os.path.exists(path)
        self._pdf_exists_cache[path] = ok
        return ok

    def _status_auditoria(self, item):
        if item["sem_pdf"] and item["sem_comprador"]:
            return "Critico"
        if item["sem_pdf"]:
            return "Sem PDF"
        if item["sem_comprador"]:
            return "Sem comprador"
        return "OK"

    def _chave_ordenacao(self, item):
        return item.get("_data_ord") or self._parse_data_pedido(item.get("data_pedido") or "")

    def _normalizar_itens(self, itens_texto):
        itens = []
        for bruto in itens_texto.split("|"):
            txt = re.sub(r"\s+", " ", bruto).strip()
            if txt:
                itens.append(txt)
        return itens

    def _resolver_pdf(self, item):
        bulk = getattr(self, "_bulk_pdf_resolve", False)
        caminho = (item.get("caminho_pdf") or "").strip()
        if caminho:
            if bulk:
                return caminho
            if self._pdf_path_exists(caminho):
                return caminho

        numero = str(item.get("numero") or "").strip()
        if not numero:
            return ""

        if AuditoriaService._pdf_index is None:
            AuditoriaService._pdf_index = self._carregar_indice_cache()

        return self._lookup_pdf_by_numero(numero, verify_exists=not bulk)

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
        pendentes = {n: it for n, it in faltando.items() if not (it.get("pdf_rede") and self._pdf_path_exists(it.get("pdf_rede")))}
        if pendentes:
            # Busca agressiva sem poda por tokens para não perder PDFs recentes.
            encontrados += self._varrer_pdfs_agressivo(pendentes)
        self._salvar_indice_cache(AuditoriaService._pdf_index or {})

        for item in pedidos:
            item["sem_pdf"] = not self._pdf_path_exists(item.get("pdf_rede"))
            item["status_auditoria"] = self._status_auditoria(item)
        self._summary_cache = {}
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
                        self._indexar_numero_pdf(indice, numero, caminho)
        return indice

    def _norm_numero(self, numero):
        n = re.sub(r"\D+", "", str(numero or ""))
        if not n:
            return ""
        n2 = n.lstrip("0")
        return n2 or "0"

    def _indexar_numero_pdf(self, indice, numero, caminho):
        raw = re.sub(r"\D+", "", str(numero or ""))
        if not raw:
            return
        if raw not in indice:
            indice[raw] = caminho
        norm = self._norm_numero(raw)
        if norm and norm not in indice:
            indice[norm] = caminho

    def _lookup_pdf_by_numero(self, numero, verify_exists=True):
        if AuditoriaService._pdf_index is None:
            AuditoriaService._pdf_index = {}
        indice = AuditoriaService._pdf_index
        raw = re.sub(r"\D+", "", str(numero or ""))
        if not raw:
            return ""
        norm = self._norm_numero(raw)
        candidates = []
        for key in (raw, norm):
            p = indice.get(key, "")
            if isinstance(p, str) and p.strip():
                candidates.append(p.strip())
        seen = set()
        for path in candidates:
            if path in seen:
                continue
            seen.add(path)
            if verify_exists:
                if self._pdf_path_exists(path):
                    return path
            else:
                return path
        return ""

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
        padrao_numero = re.compile(r"(?<!\d)(\d{2,})(?!\d)")
        roots = resolve_pdf_roots()

        numeros_faltando = {re.sub(r"\D+", "", k): k for k in faltando.keys() if re.sub(r"\D+", "", k)}
        alvo_norm = {}
        for raw in list(numeros_faltando.keys()):
            alvo_norm.setdefault(self._norm_numero(raw), set()).add(raw)

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

                    texto = os.path.splitext(os.path.join(dirpath, filename))[0]
                    candidatos = padrao_numero.findall(texto)
                    if not candidatos:
                        continue
                    inter = set()
                    for c in candidatos:
                        c_raw = re.sub(r"\D+", "", c)
                        c_norm = self._norm_numero(c_raw)
                        if c_raw in numeros_faltando:
                            inter.add(c_raw)
                        for hit in alvo_norm.get(c_norm, set()):
                            if hit in numeros_faltando:
                                inter.add(hit)
                    if not inter:
                        continue

                    caminho = os.path.join(dirpath, filename)
                    for numero_raw in inter:
                        self._indexar_numero_pdf(indice, numero_raw, caminho)
                        item = faltando[numeros_faltando[numero_raw]]
                        item["pdf_rede"] = caminho
                        numeros_faltando.pop(numero_raw, None)
                        encontrados += 1
        return encontrados

    def _varrer_pdfs_agressivo(self, faltando):
        if AuditoriaService._pdf_index is None:
            AuditoriaService._pdf_index = self._carregar_indice_cache()
        indice = AuditoriaService._pdf_index

        # 1) Primeiro tenta resolver pelo índice já existente, com normalização.
        encontrados = 0
        for numero, item in list(faltando.items()):
            path = self._lookup_pdf_by_numero(numero)
            if path:
                item["pdf_rede"] = path
                encontrados += 1

        pendentes = {n: it for n, it in faltando.items() if not (it.get("pdf_rede") and self._pdf_path_exists(it.get("pdf_rede")))}
        if not pendentes:
            return encontrados

        # 2) Varredura completa nas raízes para indexação profunda.
        roots = resolve_pdf_roots()
        padrao_numero = re.compile(r"(?<!\d)(\d{2,})(?!\d)")
        target_norm = {}
        for n in pendentes.keys():
            raw = re.sub(r"\D+", "", str(n or ""))
            if raw:
                target_norm.setdefault(self._norm_numero(raw), set()).add(raw)

        for root in roots:
            for dirpath, _, filenames in os.walk(root):
                for filename in filenames:
                    if not filename.lower().endswith(".pdf"):
                        continue
                    caminho = os.path.join(dirpath, filename)
                    texto = os.path.splitext(caminho)[0]
                    candidatos = padrao_numero.findall(texto)
                    if not candidatos:
                        continue
                    for c in candidatos:
                        raw = re.sub(r"\D+", "", c)
                        if not raw:
                            continue
                        self._indexar_numero_pdf(indice, raw, caminho)
                        norm = self._norm_numero(raw)
                        if norm in target_norm:
                            for target_raw in target_norm[norm]:
                                original = next((k for k in pendentes.keys() if self._norm_numero(k) == norm), None)
                                if original and not pendentes[original].get("pdf_rede"):
                                    pendentes[original]["pdf_rede"] = caminho

        for _, item in pendentes.items():
            if item.get("pdf_rede") and self._pdf_path_exists(item.get("pdf_rede")):
                encontrados += 1
        self._pdf_full_index_loaded = True
        return encontrados

    def _carregar_indice_cache(self):
        path = pdf_index_cache_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Não validar paths aqui: um único load + milhares de exists na rede travava a abertura por minutos.
                return {str(k): str(v).strip() for k, v in data.items() if isinstance(v, str) and str(v).strip()}
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
        cache_key = ("dashboard_summary", self._data_version, len(dados))
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]

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
            valor = p.get("_valor_total_float", float(p.get("valor_total") or 0))
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

        out = {
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
        self._summary_cache[cache_key] = out
        return out

    def obra_details(self, dados, obra_nome):
        cache_key = ("obra_details", self._data_version, obra_nome.strip().upper(), len(dados))
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]
        alvo = obra_nome.strip().upper()
        pedidos = [p for p in dados if (p.get("obra_nome") or "").strip().upper() == alvo]
        total = sum(p.get("_valor_total_float", float(p.get("valor_total") or 0)) for p in pedidos)
        mensal = {m: 0.0 for m in range(1, 13)}
        for p in pedidos:
            dt = self._chave_ordenacao(p)
            if dt.year != datetime.min.year:
                mensal[dt.month] += p.get("_valor_total_float", float(p.get("valor_total") or 0))
        out = {
            "pedidos": pedidos,
            "valor_total": total,
            "qtd_pedidos": len(pedidos),
            "mensal": mensal,
        }
        self._summary_cache[cache_key] = out
        return out

    def obra_resumo_executivo(self, dados, obra_nome):
        """Agrega indices de auditoria e ranking local para o painel de obra."""
        det = self.obra_details(dados, obra_nome)
        pedidos = det.get("pedidos") or []
        by_status = {}
        sem_pdf = 0
        sem_comprador = 0
        valor_forn = {}
        for p in pedidos:
            st = (p.get("status_auditoria") or "OK").strip() or "OK"
            by_status[st] = by_status.get(st, 0) + 1
            if p.get("sem_pdf"):
                sem_pdf += 1
            if p.get("sem_comprador"):
                sem_comprador += 1
            fn = (p.get("fornecedor_nome") or "SEM FORNECEDOR").strip() or "SEM FORNECEDOR"
            valor_forn[fn] = valor_forn.get(fn, 0.0) + float(p.get("valor_total") or 0)
        top_forn = sorted(valor_forn.items(), key=lambda x: x[1], reverse=True)[:8]
        nome_exibicao = ""
        for p in pedidos:
            nome_exibicao = (p.get("obra_nome") or obra_nome).strip()
            if nome_exibicao:
                break
        if not nome_exibicao:
            nome_exibicao = (obra_nome or "").strip()
        return {
            **det,
            "obra_nome_exibicao": nome_exibicao,
            "by_status": by_status,
            "sem_pdf_n": sem_pdf,
            "sem_comprador_n": sem_comprador,
            "top_fornecedores": top_forn,
        }

    def item_auditoria(self, dados, termo):
        cache_key = ("item_auditoria", self._data_version, (termo or "").strip().upper(), len(dados))
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]
        t = termo.strip().upper()
        rows = []
        for p in dados:
            valor = p.get("_valor_total_float", float(p.get("valor_total") or 0))
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
            out = {"rows": [], "stats": {}}
            self._summary_cache[cache_key] = out
            return out
        valores = [r["valor"] for r in rows]
        forn_barato = min(rows, key=lambda x: x["valor"]).get("fornecedor")
        out = {
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
        self._summary_cache[cache_key] = out
        return out

    def fornecedor_auditoria(self, dados, fornecedor):
        cache_key = ("fornecedor_auditoria", self._data_version, (fornecedor or "").strip().upper(), len(dados))
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]
        alvo = fornecedor.strip().upper()
        rows = [p for p in dados if (p.get("fornecedor_nome") or "").strip().upper() == alvo]
        total = sum(p.get("_valor_total_float", float(p.get("valor_total") or 0)) for p in rows)
        out = {
            "rows": rows,
            "total": total,
            "qtd_pedidos": len(rows),
            "obras": len({(r.get("obra_nome") or "").strip() for r in rows if (r.get("obra_nome") or "").strip()}),
            "ultima_compra": (rows[0].get("data_pedido") if rows else ""),
        }
        self._summary_cache[cache_key] = out
        return out

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

    def _nomes_obras_cadastro_json(self):
        """Chaves de obras.json (mesma fonte do sistema de pedidos)."""
        path = OBRAS_JSON_PATH
        if not path or not os.path.exists(path):
            return set()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return set()
            return {k.strip() for k in data.keys() if isinstance(k, str) and k.strip()}
        except Exception:
            return set()

    def _carregar_orcamentos_base_pedidos(self):
        # Base consolidada (pedidos de todos os compradores). Não parsear config.py do outro repositório:
        # lá o DATABASE_PATH é montado com os.path.join + usuário (BRASUL_USUARIO).
        db_path = self._resolver_db_programa_pedidos()
        if not db_path or not os.path.exists(db_path):
            obras_json = self._nomes_obras_cadastro_json()
            return sorted(obras_json), {}

        obras = set()
        obras |= self._nomes_obras_cadastro_json()
        previstos = {}
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            # Obras cadastradas no SQLite (quando existir no arquivo aberto).
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
        perfil_norm = normalize_profile(perfil)
        self.audit_store.upsert_user(nome, perfil_norm, ativo)
        self.audit_store.log("usuarios", nome, "UPSERT", "perfil", "", perfil_norm, operador)

    def salvar_usuario_com_senha(self, nome, perfil, ativo, senha, operador):
        perfil_norm = normalize_profile(perfil)
        self.audit_store.upsert_user(nome, perfil_norm, ativo, senha=senha)
        self.audit_store.log("usuarios", nome, "UPSERT", "perfil", "", perfil_norm, operador)

    def pode_atribuir_perfil(self, operador_perfil, perfil_alvo):
        allowed = set(assignable_profiles(operador_perfil))
        return normalize_profile(perfil_alvo) in allowed

    def listar_usuarios(self):
        users = self.audit_store.list_users()
        # Migração de legado: usuário/perfil antigo PATRAO -> ADMIN.
        has_admin = any((u.get("nome") or "").strip().upper() == "ADMIN" for u in users)
        for u in users:
            nome = (u.get("nome") or "").strip().upper()
            perfil = normalize_profile(u.get("perfil"))
            if nome == "PATRAO" and not has_admin:
                self.audit_store.upsert_user("ADMIN", "ADMIN", int(u.get("ativo", 1)) == 1)
                has_admin = True
            if perfil != (u.get("perfil") or "").strip().upper():
                self.audit_store.upsert_user(nome, perfil, int(u.get("ativo", 1)) == 1)
        users = self.audit_store.list_users()
        out = []
        for u in users:
            nome = (u.get("nome") or "").strip().upper()
            if nome == "PATRAO":
                continue
            u["perfil"] = normalize_profile(u.get("perfil"))
            out.append(u)
        return out

    def existe_admin(self):
        return any(is_admin(u.get("perfil")) and int(u.get("ativo", 0)) == 1 for u in self.listar_usuarios())

    def autenticar_usuario(self, nome, senha):
        return self.audit_store.verify_user_password(nome, senha)

    def usuario_tem_senha(self, nome):
        return self.audit_store.user_has_password(nome)

    def definir_senha_usuario(self, nome, senha, operador="SISTEMA"):
        self.audit_store.set_user_password(nome, senha)
        self.audit_store.log("usuarios", nome, "SET_PASSWORD", "senha_hash", "", "***", operador)

    def remover_usuario(self, nome, operador, operador_perfil):
        alvo = (nome or "").strip().upper()
        if not alvo:
            return False, "Usuário inválido."
        if not is_admin(operador_perfil):
            return False, "Somente ADMIN pode remover usuários."
        users = self.listar_usuarios()
        alvo_row = next((u for u in users if (u.get("nome") or "").strip().upper() == alvo), None)
        if not alvo_row:
            return False, "Usuário não encontrado."
        if is_admin(alvo_row.get("perfil")):
            admins = [u for u in users if is_admin(u.get("perfil")) and int(u.get("ativo", 0)) == 1]
            if len(admins) <= 1:
                return False, "Não é permitido remover o último ADMIN ativo."
        self.audit_store.delete_user(alvo)
        self.audit_store.log("usuarios", alvo, "DELETE", "", "", "", operador)
        return True, "Usuário removido com sucesso."

    def exportar_csv(self, caminho_arquivo, colunas, linhas):
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        with open(caminho_arquivo, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=colunas)
            writer.writeheader()
            for l in linhas:
                writer.writerow({c: l.get(c, "") for c in colunas})

    def shutdown(self):
        """Libera caches em memória no encerramento do app."""
        self._cache_dados = None
        self._cache_origem = ""
        self._summary_cache = {}
        self._pdf_exists_cache = {}
