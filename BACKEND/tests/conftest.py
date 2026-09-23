"""Configuração explícita do ambiente de testes; não define defaults de produção."""
import os

os.environ["OPENROUTER_MODEL"] = "mistralai/mistral-large"

os.environ["OPENROUTER_EMBEDDING_MODEL"] = "mistralai/mistral-embed-2312"
