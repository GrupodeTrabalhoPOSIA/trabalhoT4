"""Pacote reproduzível e apresentação com resultados reais ou pendências explícitas."""
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone

import pymupdf
from app.models.final_delivery import DeliveryInput
from app.services.final_delivery import RELEASE_ROOT, SCENES


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def csv_text(rows):
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        safe = []
        for item in row:
            value = str(item) if item is not None else "PENDENTE"
            safe.append("'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value)
        writer.writerow(safe)
    return "\ufeff" + output.getvalue()


def presentation(data, report, manifest):
    status = report.get("decision", "pendente").upper()
    metrics = report["metrics"]
    fmt = lambda v, suffix="%": "PENDENTE" if v is None else f"{v:.2f}{suffix}"
    slides = [
        ("Aurora Tech", "Copiloto Inteligente Corporativo\nTrabalho 6 · Entrega final\n\nVersão: " + manifest["release_id"] + "\nGate: " + status + "\n\nUma aprovação acadêmica não autoriza uso em produção."),
        ("Problema e público", "Colaboradores e gestores precisam consultar a política de trabalho híbrido.\n\nTrês tarefas: explicar regras, verificar elegibilidade e orientar segurança.\n\nO assistente não aprova exceções nem toma decisões individuais de RH."),
        ("Evolução dos trabalhos", "T1 · Comparação e escolha do Mistral Large.\nT2 · Escopo e baseline: factualidade histórica de 71,43%.\nT3 · Biblioteca TRH-01 a TRH-04.\nT4 · Triagem, especialistas, validação e fallback.\nT5 · Documentos, recuperação e protocolo de 20 casos.\nT6 · Identidade de versão, demonstração e gate auditável."),
        ("Arquitetura consolidada", "React/TypeScript > FastAPI > validação de entrada.\n\nTexto: política versionada. Documento: extração > trechos > embeddings > recuperação isolada.\n\nTRH-04 > especialista TRH-01/02/03 > modelo da configuração da release > validação > resposta, esclarecimento ou fallback.\n\nFontes e rastros técnicos acompanham as respostas. Decisões de maior impacto exigem revisão humana."),
        ("Segurança e alternativas", "Conteúdo do documento é dado não confiável, separado das regras do sistema.\nLogs registram rota, status e duração, sem corpos ou credenciais.\n\nAlternativas rejeitadas: enviar sempre o documento inteiro; tornar a base de teste adversarial uma coleção compartilhada.\n\nRiscos residuais: injeção, alucinação, ausência de OCR e dependência do provedor."),
        ("Seis cenas da demonstração", "\n".join(f"{index + 1}. {s['title']} · {s['case_id']}" for index, s in enumerate(SCENES)) + "\n\nEquipe: " + (data.demo_team[:240] or "A DEFINIR") + "\nDuração: " + (str(data.demo_minutes) + " min" if data.demo_minutes else "A DEFINIR") + "\nContingência: " + (data.contingency[:240] or "PENDENTE · gravação deve ser identificada como tal.")),
        ("Avaliação da versão final", f"Casos válidos: {metrics['count']}/20; revisados: {metrics['reviewed']}/20.\nSucesso: {fmt(metrics['success'])}\nEsquema: {fmt(metrics['format'])}\nCobertura de fonte: {fmt(metrics['source'])}\nLatência p95: {fmt(metrics['p95'], ' s')}\nCusto médio declarado: {fmt(metrics['cost'], ' USD')}.\nRubrica: {report['reviewed_pairs']}/10 casos com duas avaliações.\n\nT2: sete casos; T6: vinte. Populações diferentes impedem delta direto."),
        ("Gate e riscos residuais", "Decisão registrada: " + status + "\nRecomendação por evidências: " + report["recommendation"].upper() + "\n\nResponsável: " + (data.decision.responsible or "PENDENTE") + "\nJustificativa: " + (data.decision.rationale[:500] or "Aguardando avaliação, controles e revisão humana.") + "\n\nEliminatórios: vazamento, ação não autorizada, injeção bem-sucedida ou erro factual de alto impacto."),
        ("Regressões e retrospectiva — síntese", (data.regression_analysis[:470] or "Análise de regressões PENDENTE. Registrar causa provável, impacto e decisão sem inventar resultados.") + "\n\n" + (data.retrospective[:470] or "Retrospectiva PENDENTE: manter, corrigir, priorizar e condições de produção.")),
        ("Reprodução e próximos passos", "O pacote inclui manifesto, código, entradas sintéticas, arquitetura, resultados, rubrica, riscos, roteiro e contribuições.\n\nAlterar código, modelo, parâmetros, prompts, base ou fluxo exige nova versão e reexecução dos 20 casos.\n\nCondições de produção: autenticação, governança de documentos, proteção de dados, auditoria persistente, custo observado e validação ampliada.\n\nContribuições: " + (data.contributions[:350] or "Confirmar atribuições dos integrantes.")),
    ]
    with pymupdf.open() as document:
        for index, (title, body) in enumerate(slides):
            page = document.new_page(width=960, height=540)
            page.draw_rect(page.rect, fill=(.96, .98, .97), color=None)
            page.draw_rect(pymupdf.Rect(0, 0, 12, 540), fill=(.04, .46, .39), color=None)
            page.insert_text((50, 42), "AURORA TECH  /  TRABALHO 06", fontsize=10, color=(.1, .47, .4))
            page.insert_textbox(pymupdf.Rect(50, 65, 900, 135), title, fontsize=31, fontname="hebo", color=(.07, .23, .26))
            for font_size in (17, 16, 15, 14, 13):
                shape = page.new_shape()
                remaining = shape.insert_textbox(pymupdf.Rect(50, 150, 900, 465), body, fontsize=font_size, lineheight=1.28, color=(.18, .32, .34))
                if remaining >= 0:
                    shape.commit()
                    break
            else:
                raise ValueError(f"Texto não cabe no slide {index + 1}; reduza os campos de apresentação.")
            page.insert_text((50, 510), f"{manifest['release_id']}  |  {status}  |  {index + 1:02d}/{len(slides)}", fontsize=10, color=(.35, .48, .46))
        document.set_metadata({"title": "Aurora Tech — Entrega final", "author": "Grupo Aurora Tech", "subject": manifest["release_id"]})
        return document.tobytes(garbage=4, deflate=True)


def build_package(data: DeliveryInput, report, state):
    manifest = state["manifest"]
    files = {}
    # Arquivo gerado exclusivamente a partir da lista permitida no congelamento.
    archive = RELEASE_ROOT / "source.zip"
    expected = (RELEASE_ROOT / "source.sha256").read_text().strip()
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Arquivo da versão final divergente; gere novamente a versão.")
    files["release/source.zip"] = archive.read_bytes()
    files["release/manifest.json"] = json_text(manifest)
    files["evaluation/final/evidencias.json"] = json_text(data.model_dump())
    files["evaluation/final/auditoria.json"] = json_text(report)
    files["evaluation/final/gate.json"] = json_text({"release_id": manifest["release_id"], "decision": report.get("decision", "pendente"), "recorded": report["recorded"], "declaration": data.decision.model_dump(), "exported_at": datetime.now(timezone.utc).isoformat()})
    selected_ids = {r["execution_id"] for r in report["rows"] if r["execution_id"]}
    selected_runs = []
    for run in data.runs:
        if run.execution_id in selected_ids:
            selected_runs.append(run)
            selected_ids.remove(run.execution_id)
    files["evaluation/final/resultados.csv"] = csv_text([["id", "execucao", "versao", "finalidade", "cena", "modelo", "pergunta", "saida", "status", "latencia_ms", "sucesso", "eliminatorio"], *[[r.case_id, r.execution_id, r.release_id, r.purpose, r.scene_id, r.model, r.question, r.answer, r.status, r.latency_ms, r.success, r.critical] for r in selected_runs]])
    files["evaluation/final/rubrica.csv"] = csv_text([["execucao", "avaliador", "relevancia", "factualidade", "completude", "clareza", "adequacao", "seguranca", "multimodal", "justificativa", "data"], *[[r.execution_id, r.evaluator, *r.scores, r.notes, r.recorded_at] for r in data.reviews]])
    files["evaluation/final/analise.md"] = "# Comparação e regressões\n\n" + (data.regression_analysis or "PENDENTE") + "\n\n## Métricas\n\n```json\n" + json_text({"baseline": report.get("baseline"), "candidate": report.get("candidate_metrics"), "final": report["metrics"], "subgroups": report["groups"], "rubric": report["rubric"], "regressions": report["regressions"]}) + "\n```\n\nBaseline T2: sete casos; não comparar diretamente com os vinte casos finais. Custos são valores observados declarados pelo grupo, acompanhados de referência. Ausências não equivalem a zero.\n"
    files["risks/matriz_final.json"] = json_text({"release_id": manifest["release_id"], "controls": [r.model_dump() for r in data.risks], "audit": report["risk_checks"]})
    files["demo/ensaio.md"] = f"# Ensaio\n\nEquipe: {data.demo_team or 'PENDENTE'}\n\nDuração: {data.demo_minutes or 'PENDENTE'} minutos\n\n{data.rehearsal_notes or 'PENDENTE'}\n\n## Contingência\n\n{data.contingency or 'PENDENTE'}\n"
    files["CONTRIBUTIONS.md"] = "# Contribuições declaradas\n\n" + (data.contributions or "PENDENTE: o grupo deve confirmar atribuições individuais.")
    files["retrospectiva.md"] = "# Retrospectiva\n\n" + (data.retrospective or "PENDENTE: manter, corrigir, priorizar e condições para produção.")
    files["apresentacao.pdf"] = presentation(data, report, manifest)
    with zipfile.ZipFile(io.BytesIO(archive.read_bytes())) as source:
        for name in source.namelist():
            if name.startswith("BACKEND/prompts/"):
                files[name.removeprefix("BACKEND/")] = source.read(name)
    for item in (RELEASE_ROOT / "docs").glob("*.md"):
        files[{"arquitetura.md": "architecture/decisoes.md", "roteiro.md": "demo/roteiro.md", "guia.md": "README.md"}.get(item.name, item.name)] = item.read_bytes()
    diagram = RELEASE_ROOT / "docs" / "arquitetura.svg"
    if diagram.is_file(): files["architecture/arquitetura.svg"] = diagram.read_bytes()
    files["tests/casos.json"] = (RELEASE_ROOT / "cases.json").read_bytes()
    for fixture in manifest["fixtures"]:
        files[f"demo/entradas/{fixture}"] = (RELEASE_ROOT / "fixtures" / fixture).read_bytes()
    files["STATUS.md"] = f"# Estado do pacote\n\nVersão: {manifest['release_id']}\n\nGate: {report.get('decision', 'pendente').upper()}\n\n" + ("Decisão registrada pelo grupo. Aprovação acadêmica não autoriza produção." if report["recorded"] else "RASCUNHO: existem pendências. Este pacote não comprova aprovação acadêmica.") + "\n\n" + "\n".join("- " + issue for issue in report["issues"])
    files["checksums.sha256"] = "\n".join(hashlib.sha256(content.encode() if isinstance(content, str) else content).hexdigest() + "  " + name for name, content in sorted(files.items()))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
        for name, content in files.items(): package.writestr(name, content)
    return output.getvalue()
