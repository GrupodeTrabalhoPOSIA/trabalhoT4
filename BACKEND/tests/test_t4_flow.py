from pathlib import Path
import asyncio
from app.services.t4 import PromptRegistry, T4FlowService

PROMPTS = Path(__file__).parents[1] / "prompts" / "templates"
KB = (Path(__file__).parents[1] / "knowledge" / "politica_aurora_tech.txt").read_text(encoding="utf-8")

class ScriptedLLM:
    def __init__(self, outputs): self.outputs=list(outputs); self.calls=[]
    async def complete(self, messages): self.calls.append(messages); return self.outputs.pop(0)

def service(outputs): return T4FlowService(llm_client=ScriptedLLM(outputs), prompt_registry=PromptRegistry(PROMPTS), knowledge_base=KB)

def test_routes_rule_and_validates_output():
    s=service(['{"prompt_destino":"TRH-01","confianca":0.98,"motivo":"regra"}', 'Resposta: Até dois dias.\nRegra aplicada: Colaboradores elegíveis poderão trabalhar remotamente até dois dias por semana.\nPróximo passo: Definir os dias com o gestor.'])
    r=asyncio.run(s.run('Quantos dias posso trabalhar remotamente?'))
    assert (r.route,r.prompt_id,r.valid,r.retries,r.status)==('TRH-01','TRH-01',True,0,'respondido')

def test_missing_eligibility_data_asks_user_without_specialist_call():
    s=service(['{"prompt_destino":"TRH-02","confianca":0.95,"motivo":"elegibilidade"}'])
    r=asyncio.run(s.run('Sou elegível ao trabalho híbrido?'))
    assert r.status=='perguntar_dado_ausente' and r.prompt_id=='TRH-02'

def test_out_of_scope_is_safely_refused():
    s=service(['{"prompt_destino":"FORA_ESCOPO","confianca":0.99,"motivo":"fora"}'])
    r=asyncio.run(s.run('Qual é o cardápio do refeitório?'))
    assert r.status=='recusado_fora_escopo'

def test_router_invalid_json_retries_once():
    s=service(['não é json','{"prompt_destino":"TRH-03","confianca":0.9,"motivo":"segurança"}', 'Resposta: Use autenticação multifator.\nRegra aplicada: O acesso requer autenticação multifator e dispositivo gerenciado.\nPróximo passo: Usar dispositivo gerenciado.'])
    r=asyncio.run(s.run('Como devo acessar os documentos?'))
    assert r.route=='TRH-03' and r.retries==1 and r.valid

def test_specialist_invalid_format_retries_once():
    s=service(['{"prompt_destino":"TRH-01","confianca":0.9,"motivo":"regra"}', 'Até dois dias.', 'Resposta: Até dois dias.\nRegra aplicada: Até dois dias por semana.\nPróximo passo: Definir com o gestor.'])
    r=asyncio.run(s.run('Quantos dias remotos?'))
    assert r.retries==1 and r.valid

def test_second_invalid_specialist_output_uses_fallback():
    s=service(['{"prompt_destino":"TRH-03","confianca":0.9,"motivo":"segurança"}', 'inválida', 'ainda inválida'])
    r=asyncio.run(s.run('Como acesso os documentos?'))
    assert not r.valid and r.status=='fallback_validacao'
