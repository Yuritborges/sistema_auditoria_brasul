import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime
import re
import json
import csv
import sqlite3
import logging

from app.config import (
    BASE_DIR,
    BASE_REDE_PEDIDOS,
    AUDITORIA_DB_COPY_ON_FORCE_RELOAD,
    resolve_consolidar_argv,
    resolve_db_path,
    resolve_pdf_roots,
    pdf_index_cache_path,
)

LOCK_CONSOLIDAR_REDE = os.path.join(BASE_REDE_PEDIDOS, ".consolidar_rede.lock")
from app.core.auth import assignable_profiles, is_admin, normalize_profile
from app.core.audit_store import AuditStore
from app.data.auditoria_repository import AuditoriaRepository


class AuditoriaService:
    _pdf_index = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audit_store = AuditStore(BASE_DIR)
        self._cache_dados = None
        self._cache_origem = ""
        self._cache_db_path = ""
        self._cache_db_mtime = None
        self._cache_db_size = None
        self._pdf_exists_cache = {}
        self._summary_cache = {}
        self._data_version = 0
        self._pdf_full_index_loaded = False

    def _cache_still_valid(self, db_path):
        """Evita reler o SQLite sem necessidade, mas detecta consolidacao (mtime do .db)."""
        if not db_path:
            return True
        if not os.path.isfile(db_path):
            return False
        try:
            st = os.stat(db_path)
            return (
                db_path == self._cache_db_path
                and st.st_mtime == self._cache_db_mtime
                and st.st_size == self._cache_db_size
            )
        except OSError:
            return False

    def invalidate_consolidated_cache(self):
        """O próximo carregar(force=False) ignora a snapshot em RAM e volta a abrir o .db no disco.

        Usado pelo polling periódico: em pastas de rede o stat(mtime/size) pode ficar obsoleto
        enquanto o SQLite já tem linhas novas; sem isto o timer de 30s parece «não fazer nada».
        """
        self._cache_dados = None
        self._cache_db_mtime = None
        self._cache_db_size = None

    def is_demo_mode(self) -> bool:
        return not bool(resolve_db_path())

    def needs_reload(self, force=False) -> bool:
        """Evita reler/copiar o .db quando o consolidado na rede não mudou."""
        db_path = resolve_db_path()
        if not db_path or self._cache_dados is None:
            return True
        if not force:
            return not self._cache_still_valid(db_path)
        return not self._cache_still_valid(db_path)

    def sincronizar_consolidado_pedidos(self):
        """Corre o consolidar_rede do sistema de pedidos (mesma pasta Z:\\0 OBRAS) e devolve (ok, mensagem_erro)."""
        argv = resolve_consolidar_argv()
        if not argv:
            return False, (
                "Consolidador nao disponivel: consolidar_rede.py nao encontrado ou falta python.exe "
                "(em .exe empacotado use AUDITORIA_CONSOLIDAR_PYTHON ou .venv na pasta do projeto na rede)."
            )
        if os.path.isfile(LOCK_CONSOLIDAR_REDE):
            return False, (
                "Consolidacao em andamento no sistema de pedidos (.consolidar_rede.lock). "
                "Aguarde alguns segundos e tente novamente."
            )
        exe0 = os.path.normcase(os.path.abspath(argv[0]))
        if getattr(sys, "frozen", False) and exe0 == os.path.normcase(os.path.abspath(sys.executable)):
            return (
                False,
                "Configuracao invalida: o primeiro argumento do subprocesso nao pode ser o .exe da auditoria.",
            )
        cwd = os.path.dirname(argv[1])
        run_kw = {
            "args": argv,
            "cwd": cwd,
            "capture_output": True,
            "text": True,
            "timeout": 900,
        }
        if sys.platform == "win32":
            run_kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            cp = subprocess.run(**run_kw)
        except subprocess.TimeoutExpired:
            return False, "Tempo esgotado (15 min) ao consolidar."
        except OSError as e:
            return False, str(e)
        if cp.returncode != 0:
            tail = (cp.stderr or cp.stdout or "").strip()
            if len(tail) > 1500:
                tail = tail[-1500:]
            return False, tail or f"Consolidacao terminou com codigo {cp.returncode}."
        return True, ""

    def carregar(self, force=False):
        db_path = resolve_db_path()
        if not force and self._cache_dados is not None and self._cache_still_valid(db_path):
            return [dict(item) for item in self._cache_dados], self._cache_origem

        self._pdf_exists_cache = {}
        self._summary_cache = {}

        tmp_db = None
        read_path = db_path
        skip_copy = db_path and self._cache_still_valid(db_path)
        if (
            db_path
            and os.path.isfile(db_path)
            and force
            and AUDITORIA_DB_COPY_ON_FORCE_RELOAD
            and not skip_copy
        ):
            try:
                fd, tmp_db = tempfile.mkstemp(prefix="auditoria_cotacao_", suffix=".db")
                os.close(fd)
                shutil.copy2(db_path, tmp_db)
                read_path = tmp_db
                self.logger.info(
                    "Banco consolidado lido a partir de copia local temporaria (evita cache SMB). Origem: %s",
                    db_path,
                )
            except OSError:
                self.logger.exception("Falha ao copiar banco para temporario; leitura direta do caminho de rede")
                if tmp_db:
                    try:
                        os.remove(tmp_db)
                    except OSError:
                        pass
                    tmp_db = None
                read_path = db_path

        try:
            if read_path:
                repo = AuditoriaRepository(read_path)
                dados = repo.listar_pedidos()
                itens_por_pedido = repo.listar_itens_por_pedido()
                for item in dados:
                    pid = item.get("pedido_id")
                    item["itens_detalhe"] = itens_por_pedido.get(pid, [])
                origem = f"Banco real: {db_path}"
            else:
                dados = self._dados_demo()
                origem = "Modo demonstracao: banco consolidado nao encontrado"
        finally:
            if tmp_db:
                try:
                    os.remove(tmp_db)
                except OSError:
                    self.logger.warning("Nao foi possivel apagar temporario %s", tmp_db)

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
        if db_path and os.path.isfile(db_path):
            try:
                st = os.stat(db_path)
                self._cache_db_path = db_path
                self._cache_db_mtime = st.st_mtime
                self._cache_db_size = st.st_size
            except OSError:
                self._cache_db_path = db_path
                self._cache_db_mtime = None
                self._cache_db_size = None
        else:
            self._cache_db_path = ""
            self._cache_db_mtime = None
            self._cache_db_size = None
        return [dict(item) for item in dados], origem

    def _enriquecer_item(self, item):
        item["_valor_total_float"] = float(item.get("valor_total") or 0)
        item["_data_ord"] = self._data_referencia_pedido(item)
        item["origem"] = (item.get("comprador") or "").strip().upper()
        item["pdf_rede"] = self._resolver_pdf(item)
        if getattr(self, "_bulk_pdf_resolve", False):
            item["sem_pdf"] = not bool((item.get("pdf_rede") or "").strip())
        else:
            item["sem_pdf"] = not self._pdf_path_exists(item.get("pdf_rede"))
        item["sem_comprador"] = not (item.get("comprador") or "").strip()
        item["status_auditoria"] = self._status_auditoria(item)
        item["itens_lista"] = self._normalizar_itens(item.get("itens_texto") or "")

    def _data_referencia_pedido(self, item):
        """Data para ordenacao e KPIs: data_pedido exibida; se invalida, usa emitido_em do banco."""
        dt = self._parse_data_bruta(item.get("data_pedido") or "")
        if dt != datetime.min:
            return dt
        return self._parse_emitido_em(item.get("emitido_em"))

    def _parse_data_bruta(self, texto):
        """Parse flexivel: brasileiro DD/MM/AAAA ou ISO (como gravado pelo SQLite/pedidos)."""
        if isinstance(texto, datetime):
            dt = texto
            if dt.tzinfo is not None:
                dt = dt.astimezone().replace(tzinfo=None)
            return dt
        if isinstance(texto, date):
            return datetime.combine(texto, datetime.min.time())
        txt = (texto if isinstance(texto, str) else str(texto or "")).strip()
        if not txt:
            return datetime.min
        fmts = (
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        )
        for fmt in fmts:
            try:
                return datetime.strptime(txt, fmt)
            except Exception:
                pass
        if len(txt) >= 10 and txt[4] == "-" and txt[7] == "-":
            try:
                return datetime.strptime(txt[:10], "%Y-%m-%d")
            except Exception:
                pass
        try:
            return datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    def _parse_emitido_em(self, raw):
        if raw is None:
            return datetime.min
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, (int, float)):
            return self._from_unix_ts(raw)
        s = str(raw).strip()
        if not s:
            return datetime.min
        d = self._parse_data_bruta(s)
        if d != datetime.min:
            return d
        try:
            n = float(s)
            return self._from_unix_ts(n)
        except Exception:
            return datetime.min

    def _from_unix_ts(self, n):
        try:
            v = float(n)
            if v > 1e12:
                v = v / 1000.0
            if v <= 0:
                return datetime.min
            return datetime.fromtimestamp(v)
        except Exception:
            return datetime.min

    def _parse_data_pedido(self, texto):
        return self._parse_data_bruta(texto or "")

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
            return "Crítico"
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
            self.logger.exception("Falha ao carregar índice de PDF")
        return {}

    def _salvar_indice_cache(self, indice):
        path = pdf_index_cache_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(indice, f, ensure_ascii=False)
        except Exception:
            self.logger.exception("Falha ao salvar índice de PDF")

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

    def _linhas_item_do_pedido(self, pedido, termo_upper):
        obra = (pedido.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"
        fornecedor = (pedido.get("fornecedor_nome") or "SEM FORNECEDOR").strip() or "SEM FORNECEDOR"
        data = pedido.get("data_pedido") or ""
        numero = str(pedido.get("numero") or "").strip()
        detalhe = pedido.get("itens_detalhe") or []
        linhas = []
        if detalhe:
            for lin in detalhe:
                desc = (lin.get("descricao") or "").strip()
                if not desc:
                    continue
                if termo_upper and termo_upper not in desc.upper():
                    continue
                linhas.append(
                    {
                        "item": desc,
                        "obra": obra,
                        "fornecedor": fornecedor,
                        "quantidade": float(lin.get("quantidade") or 0),
                        "unidade": (lin.get("unidade") or "").strip().upper(),
                        "valor_unitario": float(lin.get("valor_unitario") or 0),
                        "valor": float(lin.get("valor_total") or 0),
                        "data": data,
                        "numero_pedido": numero,
                    }
                )
            return linhas
        for desc in pedido.get("itens_lista") or []:
            if termo_upper and termo_upper not in desc.upper():
                continue
            linhas.append(
                {
                    "item": desc,
                    "obra": obra,
                    "fornecedor": fornecedor,
                    "quantidade": 0.0,
                    "unidade": "",
                    "valor_unitario": 0.0,
                    "valor": pedido.get("_valor_total_float", float(pedido.get("valor_total") or 0)),
                    "data": data,
                    "numero_pedido": numero,
                }
            )
        return linhas

    @staticmethod
    def _totais_quantidade_por_obra(rows):
        """Soma quantidades por obra e unidade (nao mistura unidades diferentes)."""
        bucket = {}
        for r in rows:
            obra = r.get("obra") or "SEM OBRA"
            un = (r.get("unidade") or "").strip().upper() or "—"
            qtd = float(r.get("quantidade") or 0)
            if qtd <= 0:
                continue
            bucket.setdefault(obra, {})
            bucket[obra][un] = bucket[obra].get(un, 0.0) + qtd
        totais = []
        for obra in sorted(bucket.keys()):
            for un, total in sorted(bucket[obra].items(), key=lambda x: (-x[1], x[0])):
                totais.append({"obra": obra, "unidade": un, "total": total})
        return totais

    def _filtrar_pedidos_item_auditoria(self, dados, filtros):
        """Mesmos critérios do módulo Pedidos, antes de expandir linhas de item."""
        comprador = (filtros.get("comprador") or "TODOS").strip().upper()
        obra = (filtros.get("obra") or "TODAS").strip().upper()
        status = (filtros.get("status") or "TODOS").strip().upper()
        fornecedor = (filtros.get("fornecedor") or "TODOS").strip().upper()
        item_txt = (filtros.get("item") or "").strip().upper()
        d_ini = filtros.get("data_ini")
        d_fim = filtros.get("data_fim")
        if d_ini and d_fim and d_ini > d_fim:
            d_ini, d_fim = d_fim, d_ini
        out = []
        for d in dados:
            if comprador != "TODOS" and comprador != (d.get("comprador") or "").strip().upper():
                continue
            if obra != "TODAS" and obra != (d.get("obra_nome") or "").strip().upper():
                continue
            st = (d.get("status_auditoria") or "").strip().upper()
            if status != "TODOS" and status != st:
                continue
            if (
                fornecedor
                and fornecedor != "TODOS"
                and fornecedor not in (d.get("fornecedor_nome") or "").upper()
            ):
                continue
            if item_txt and item_txt not in (d.get("itens_texto") or "").upper():
                continue
            if d_ini and d_fim:
                dt = self._data_referencia_pedido(d)
                if dt == datetime.min:
                    continue
                pd = dt.date()
                if pd < d_ini or pd > d_fim:
                    continue
            out.append(d)
        return out

    def item_auditoria(self, dados, filtros=None):
        filtros = filtros or {}
        t = (filtros.get("item") or "").strip().upper()
        obra_alvo = (filtros.get("obra") or "TODAS").strip().upper()
        cache_key = (
            "item_auditoria",
            self._data_version,
            t,
            obra_alvo,
            (filtros.get("comprador") or "").strip().upper(),
            (filtros.get("status") or "").strip().upper(),
            (filtros.get("fornecedor") or "").strip().upper(),
            str(filtros.get("data_ini")),
            str(filtros.get("data_fim")),
            len(dados),
        )
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]
        pedidos = self._filtrar_pedidos_item_auditoria(dados, filtros)
        rows = []
        for p in pedidos:
            rows.extend(self._linhas_item_do_pedido(p, t))
        if not rows:
            out = {"rows": [], "stats": {}, "totais_obra": []}
            self._summary_cache[cache_key] = out
            return out
        valores_unit = [r["valor_unitario"] for r in rows if r.get("valor_unitario")]
        valores_linha = [r["valor"] for r in rows]
        forn_por_unit = {}
        for r in rows:
            if r.get("valor_unitario", 0) <= 0:
                continue
            fn = r.get("fornecedor") or ""
            if fn not in forn_por_unit or r["valor_unitario"] < forn_por_unit[fn]:
                forn_por_unit[fn] = r["valor_unitario"]
        forn_barato = min(forn_por_unit, key=forn_por_unit.get) if forn_por_unit else "-"
        totais_obra = self._totais_quantidade_por_obra(rows)
        total_obra_filtrada = []
        if obra_alvo and obra_alvo != "TODAS":
            total_obra_filtrada = [x for x in totais_obra if (x.get("obra") or "").upper() == obra_alvo]
        out = {
            "rows": rows,
            "totais_obra": totais_obra,
            "stats": {
                "qtd": len(rows),
                "obras": len({r["obra"] for r in rows}),
                "preco_medio_unit": (sum(valores_unit) / len(valores_unit)) if valores_unit else 0,
                "preco_min_unit": min(valores_unit) if valores_unit else 0,
                "preco_max_unit": max(valores_unit) if valores_unit else 0,
                "valor_total_linhas": sum(valores_linha),
                "fornecedor_mais_barato": forn_barato,
                "total_obra_filtrada": total_obra_filtrada,
            },
        }
        self._summary_cache[cache_key] = out
        return out

    @staticmethod
    def _pedido_datetime_ord(p):
        d = p.get("_data_ord")
        if isinstance(d, datetime):
            return d
        txt = (p.get("data_pedido") or "").strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(txt, fmt)
            except ValueError:
                continue
        return datetime.min

    def fornecedor_auditoria(self, dados, fornecedor):
        cache_key = ("fornecedor_auditoria", self._data_version, (fornecedor or "").strip().upper(), len(dados))
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]
        alvo = fornecedor.strip().upper()
        rows = [p for p in dados if (p.get("fornecedor_nome") or "").strip().upper() == alvo]
        rows.sort(key=self._pedido_datetime_ord, reverse=True)
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
        if not users:
            # Bootstrap mínimo: garante usuário ADMIN local para primeiro acesso.
            self.audit_store.upsert_user("ADMIN", "ADMIN", True)
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

    def limpar_senha_para_primeiro_acesso(self, nome, operador="SISTEMA"):
        """Zera a senha gravada; na proxima abertura o usuario define nova senha no login."""
        nome_norm = (nome or "").strip().upper()
        self.audit_store.clear_user_password(nome_norm)
        self.audit_store.log("usuarios", nome_norm, "CLEAR_PASSWORD", "senha_hash", "***", "", operador)

    def definir_senha_usuario(self, nome, senha, operador="SISTEMA"):
        nome_norm = (nome or "").strip().upper()
        users = self.listar_usuarios()
        row = next((u for u in users if (u.get("nome") or "").strip().upper() == nome_norm), None)
        if row is None:
            perfil = "ADMIN" if nome_norm == "ADMIN" and not self.existe_admin() else "COMPRADOR"
            self.audit_store.upsert_user(nome_norm, perfil, True, senha=senha)
        else:
            self.audit_store.set_user_password(nome_norm, senha)
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

    # ---------- contratos ----------
    def listar_contratos(self):
        contratos = self.audit_store.list_contracts()
        add_by_contract = {}
        for ad in self.audit_store.list_addenda():
            cid = int(ad.get("contrato_id") or 0)
            add_by_contract[cid] = add_by_contract.get(cid, 0.0) + float(ad.get("valor") or 0)
        for c in contratos:
            base = float(c.get("valor_global") or 0)
            acresc = add_by_contract.get(int(c.get("id") or 0), 0.0)
            c["valor_atualizado"] = base + acresc
        return contratos

    def salvar_contrato(self, numero, obra, objeto, valor_global, prazo_inicio, prazo_fim, operador):
        self.audit_store.upsert_contract(numero, obra, objeto, valor_global, prazo_inicio, prazo_fim)
        self.audit_store.log("contratos", numero, "UPSERT", "valor_global", "", valor_global, operador)

    def remover_contrato(self, contract_id, operador):
        self.audit_store.delete_contract(contract_id)
        self.audit_store.log("contratos", contract_id, "DELETE", "", "", "", operador)

    def listar_aditivos(self, contrato_id=None):
        return self.audit_store.list_addenda(contrato_id)

    def salvar_aditivo(self, contrato_id, tipo, descricao, valor, prazo_dias, data_aditivo, operador):
        self.audit_store.add_contract_addendum(contrato_id, tipo, descricao, valor, prazo_dias, data_aditivo)
        self.audit_store.log("aditivos_contrato", contrato_id, "UPSERT", "valor", "", valor, operador)

    # ---------- medições ----------
    def listar_medicoes(self, contrato_id=None):
        return self.audit_store.list_medicoes(contrato_id)

    def salvar_medicao(self, contrato_id, obra, competencia, percentual_fisico, valor_medido, responsavel, observacoes, operador):
        self.audit_store.upsert_medicao(
            contrato_id,
            obra,
            competencia,
            percentual_fisico,
            valor_medido,
            responsavel,
            observacoes,
        )
        self.audit_store.log("medicoes", f"{contrato_id}:{competencia}", "UPSERT", "valor_medido", "", valor_medido, operador)

    def resumo_fisico_financeiro(self):
        contratos = self.listar_contratos()
        by_id = {int(c.get("id") or 0): c for c in contratos}
        out = []
        for m in self.listar_medicoes():
            cid = int(m.get("contrato_id") or 0)
            contrato = by_id.get(cid, {})
            valor_contrato = float(contrato.get("valor_atualizado") or contrato.get("valor_global") or 0)
            valor_medido = float(m.get("valor_medido") or 0)
            perc_fin = (valor_medido / valor_contrato * 100) if valor_contrato else 0
            out.append(
                {
                    **m,
                    "contrato_numero": contrato.get("numero", ""),
                    "valor_contrato": valor_contrato,
                    "percentual_financeiro": perc_fin,
                    "gap_fisico_financeiro": float(m.get("percentual_fisico") or 0) - perc_fin,
                }
            )
        return out

    # ---------- notas fiscais / conciliação ----------
    def listar_notas_fiscais(self):
        return self.audit_store.list_notas_fiscais()

    def salvar_nota_fiscal(
        self,
        numero_nf,
        pedido_numero,
        contrato_id,
        obra,
        fornecedor,
        valor,
        data_emissao,
        status_conciliacao,
        justificativa,
        operador,
    ):
        self.audit_store.upsert_nota_fiscal(
            numero_nf,
            pedido_numero,
            contrato_id,
            obra,
            fornecedor,
            valor,
            data_emissao,
            status_conciliacao,
            justificativa,
        )
        self.audit_store.log("notas_fiscais", numero_nf, "UPSERT", "valor", "", valor, operador)

    def conciliar_nf_pedidos_medicoes(self, dados_pedidos):
        pedidos_by_num = {str(p.get("numero") or "").strip(): p for p in (dados_pedidos or [])}
        med_by_contract = {}
        for m in self.listar_medicoes():
            cid = int(m.get("contrato_id") or 0)
            med_by_contract[cid] = med_by_contract.get(cid, 0.0) + float(m.get("valor_medido") or 0)
        divergencias = []
        for nf in self.listar_notas_fiscais():
            flags = []
            pedido_num = str(nf.get("pedido_numero") or "").strip()
            valor_nf = float(nf.get("valor") or 0)
            pedido = pedidos_by_num.get(pedido_num)
            if not pedido:
                flags.append("PEDIDO_NAO_ENCONTRADO")
            else:
                if abs(float(pedido.get("valor_total") or 0) - valor_nf) > 0.01:
                    flags.append("VALOR_DIVERGENTE_PEDIDO")
                forn_nf = (nf.get("fornecedor") or "").strip().upper()
                forn_p = (pedido.get("fornecedor_nome") or "").strip().upper()
                if forn_nf and forn_p and forn_nf != forn_p:
                    flags.append("FORNECEDOR_DIVERGENTE")
            cid = int(nf.get("contrato_id") or 0)
            if cid and valor_nf > med_by_contract.get(cid, 0.0):
                flags.append("VALOR_NF_ACIMA_MEDIDO")
            divergencias.append(
                {
                    **nf,
                    "flags": flags,
                    "status": "DIVERGENTE" if flags else "OK",
                }
            )
        return divergencias

    # ---------- sinapi ----------
    def importar_sinapi_csv(self, csv_path, competencia, uf="SP"):
        total = 0
        self.audit_store.clear_sinapi_competencia(competencia, uf)
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo = (row.get("codigo") or row.get("CODIGO") or row.get("insumo") or "").strip()
                descricao = (row.get("descricao") or row.get("DESCRICAO") or "").strip()
                unidade = (row.get("unidade") or row.get("UNIDADE") or "").strip()
                preco_raw = (
                    row.get("preco")
                    or row.get("PRECO")
                    or row.get("preco_referencia")
                    or row.get("VALOR")
                    or "0"
                )
                preco = float(str(preco_raw).replace(".", "").replace(",", "."))
                if not codigo:
                    continue
                self.audit_store.upsert_sinapi(competencia, codigo, descricao, unidade, preco, uf)
                total += 1
        return total

    def listar_sinapi(self, competencia=None, uf="SP"):
        return self.audit_store.list_sinapi(competencia, uf)

    def comparar_itens_com_sinapi(self, dados_pedidos, competencia, uf="SP"):
        sinapi = self.audit_store.list_sinapi(competencia, uf)
        by_code = {str(r.get("codigo") or "").strip().upper(): r for r in sinapi}
        rows = []
        for p in (dados_pedidos or []):
            itens = p.get("itens_lista") or []
            valor_total = float(p.get("valor_total") or 0)
            valor_item = (valor_total / len(itens)) if itens else 0
            for it in itens:
                code = re.sub(r"\D+", "", it).upper()
                ref = by_code.get(code)
                if not ref:
                    continue
                preco_ref = float(ref.get("preco") or 0)
                variacao = ((valor_item - preco_ref) / preco_ref * 100) if preco_ref else 0
                rows.append(
                    {
                        "pedido": p.get("numero") or "",
                        "item": it,
                        "codigo_sinapi": code,
                        "preco_item_estimado": valor_item,
                        "preco_sinapi": preco_ref,
                        "variacao_percentual": variacao,
                        "alerta": "ALTO_DESVIO" if abs(variacao) > 25 else "OK",
                    }
                )
        return rows

    # ---------- fiscalização ----------
    def listar_vistorias(self):
        return self.audit_store.list_vistorias()

    def salvar_vistoria(self, obra, contrato_id, data_vistoria, responsavel, resumo, status, operador):
        vid = self.audit_store.add_vistoria(obra, contrato_id, data_vistoria, responsavel, resumo, status)
        self.audit_store.log("vistorias", vid, "UPSERT", "status", "", status, operador)
        return vid

    def listar_rncs(self):
        return self.audit_store.list_rncs()

    def salvar_rnc(self, vistoria_id, obra, descricao, prazo_solucao, acao_corretiva, operador):
        rid = self.audit_store.add_rnc(vistoria_id, obra, descricao, prazo_solucao, acao_corretiva)
        self.audit_store.log("rnc", rid, "UPSERT", "status", "", "ABERTA", operador)
        return rid

    def atualizar_rnc_status(self, rnc_id, status, acao_corretiva, operador):
        resolvida_em = datetime.now().strftime("%d/%m/%Y") if (status or "").strip().upper() == "RESOLVIDA" else ""
        self.audit_store.set_rnc_status(rnc_id, status, acao_corretiva, resolvida_em)
        self.audit_store.log("rnc", rnc_id, "STATUS", "status", "", status, operador)

    def anexar_rnc(self, rnc_id, caminho_arquivo, tipo, operador):
        self.audit_store.add_rnc_anexo(rnc_id, caminho_arquivo, tipo)
        self.audit_store.log("rnc_anexos", rnc_id, "ADD", "arquivo", "", caminho_arquivo, operador)

    def listar_rnc_anexos(self, rnc_id=None):
        return self.audit_store.list_rnc_anexos(rnc_id)

    # ---------- relatório mensal ----------
    def gerar_relatorio_mensal_pdf(self, caminho_arquivo, periodo_ini, periodo_fim, dados):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception as exc:
            raise RuntimeError("Dependência reportlab não instalada. Execute: pip install reportlab") from exc

        c = canvas.Canvas(caminho_arquivo, pagesize=A4)
        width, height = A4
        y = height - 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Relatório Mensal de Auditoria")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Período: {periodo_ini} a {periodo_fim}")
        y -= 20
        resumo = self.dashboard_summary(dados)
        c.drawString(40, y, f"Total ano: R$ {resumo['total_ano']:.2f} | Pendentes: {resumo['pendentes']} | Sem PDF: {resumo['sem_pdf']}")
        y -= 25
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Top obras")
        y -= 16
        c.setFont("Helvetica", 10)
        for obra, valor in resumo.get("top_obras", [])[:10]:
            c.drawString(48, y, f"- {obra}: R$ {valor:.2f}")
            y -= 14
            if y < 80:
                c.showPage()
                y = height - 40
        c.save()

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
