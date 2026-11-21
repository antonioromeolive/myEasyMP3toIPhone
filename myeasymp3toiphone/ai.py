# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""I fornitori di AI (Ollama, Azure OpenAI, OpenAI, Anthropic), come in myCalibreTools.

Ogni fornitore risponde a ask_json(system, user, schema): un oggetto JSON conforme allo schema. Ollama, Azure e OpenAI
si chiamano via HTTP; Anthropic con l'SDK ufficiale (pacchetto anthropic), con l'output strutturato
(output_config.format) e, sui modelli che lo prevedono, il fallback lato server quando il modello rifiuta.
"""

from __future__ import annotations

import json
import logging
import re

import requests

from .config import (
    ANTHROPIC, AZURE, DEFAULT_MODELS, DEFAULT_SCAN_PROFILE, OLLAMA, OLLAMA_LOCAL_SERVER, OPENAI, PROFILES_FILE,
    AppSettings, ProviderProfile, save_profiles,
)

log = logging.getLogger(__name__)

ANTHROPIC_MAX_TOKENS = 16000
ANTHROPIC_EFFORT = "high"
# Modelli che accettano il fallback lato server (beta server-side-fallback-2026-07-01, fallbacks="default"):
# se il modello rifiuta la richiesta, l'API la ripete su un altro modello nella stessa chiamata.
ANTHROPIC_FALLBACK_MODELS = ("claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5",
                             "claude-sonnet-5-5")
ANTHROPIC_FALLBACK_BETA = "server-side-fallback-2026-07-01"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
# Le famiglie di modelli locali preferite per la scansione, in ordine (JSON affidabile, italiano buono)
PREFERRED_LOCAL_FAMILIES = ("gemma4", "qwen3", "gemma3", "llama3", "mistral", "gpt-oss")

TEST_SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}, "colour": {"type": "string"}},
    "required": ["ok", "colour"],
    "additionalProperties": False,
}


class AIError(Exception):
    """Un errore dell'AI, con un messaggio leggibile e senza indirizzi privati."""


def parse_json_reply(text: str) -> dict:
    """La risposta come oggetto JSON; accetta anche un blocco ```json … ``` intorno."""
    cleaned = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.S)
    if fenced:
        cleaned = fenced.group(1)
    try:
        data = json.loads(cleaned)
    except ValueError as exc:
        raise AIError(f"La risposta dell'AI non è JSON valido: {text[:300]!r}") from exc
    if not isinstance(data, dict):
        raise AIError(f"La risposta dell'AI non è un oggetto JSON: {text[:300]!r}")
    return data


class Provider:
    def __init__(self, profile: ProviderProfile) -> None:
        self.profile = profile

    def ask_json(self, system: str, user: str, schema: dict) -> dict:
        log.info("Richiesta AI: profilo=%s tipo=%s modello=%s caratteri=%d", self.profile.name, self.profile.kind,
                 self.profile.model or "(predefinito)", len(user))
        reply = self._ask(system, user, schema)
        log.debug("Risposta AI:\n%s", reply)
        result = parse_json_reply(reply)
        return result

    def _ask(self, system: str, user: str, schema: dict) -> str:
        raise NotImplementedError

    def list_models(self) -> list:
        result = []
        return result

    def _post(self, label: str, url: str, body: dict, headers: dict) -> dict:
        try:
            response = requests.post(url, json=body, headers=headers, timeout=self.profile.timeout)
        except requests.RequestException as exc:
            raise AIError(self.profile.without_server(f"{label}: richiesta non riuscita ({exc})")) from exc
        if response.status_code != 200:
            raise AIError(self.profile.without_server(f"{label}: errore {response.status_code}: {response.text[:500]}"))
        try:
            data = response.json()
        except ValueError as exc:
            raise AIError(f"{label}: la risposta non è quella di un'API {self.profile.kind} (indirizzo sbagliato?): "
                          f"{response.text[:300]!r}") from exc
        return data


class OllamaProvider(Provider):
    def _url(self, path: str) -> str:
        server = self.profile.server
        if not server:
            raise AIError(f"Profilo {self.profile.name!r}: nessun server ({self.profile.base_url or 'vuoto'} non ha "
                          "valore)")
        result = server.rstrip("/") + path
        return result

    def _headers(self) -> dict:
        key = self.profile.api_key
        if key:
            result = {"Authorization": f"Bearer {key}"}
        else:
            result = {}
        return result

    def _ask(self, system: str, user: str, schema: dict) -> str:
        profile = self.profile
        options = {"num_ctx": profile.num_ctx}
        if profile.temperature is not None:
            options["temperature"] = profile.temperature
        body = {
            "model": profile.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": schema,
            "stream": False,
            "options": options,
        }
        data = self._post("Ollama", self._url("/api/chat"), body, self._headers())
        result = (data.get("message") or {}).get("content", "")
        return result

    def list_models(self) -> list:
        try:
            response = requests.get(self._url("/api/tags"), timeout=10, headers=self._headers())
            response.raise_for_status()
            models = response.json().get("models", [])
        except (requests.RequestException, ValueError) as exc:
            raise AIError(f"Ollama non raggiungibile su {self.profile.server_name}: "
                          f"{self.profile.without_server(str(exc))}") from exc
        result = []
        for model in models:
            result.append(model.get("name", ""))
        result.sort()
        return result


def _openai_body(profile: ProviderProfile, system: str, user: str, schema: dict) -> dict:
    body = {
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "risposta", "schema": schema, "strict": True}},
    }
    if profile.temperature is not None:
        body["temperature"] = profile.temperature
    return body


def _openai_content(label: str, data: dict) -> str:
    choice = (data.get("choices") or [{}])[0]
    if choice.get("finish_reason") == "content_filter":
        raise AIError(f"{label}: il filtro dei contenuti ha bloccato la risposta")
    result = (choice.get("message") or {}).get("content") or ""
    return result


def azure_endpoint(base_url: str, api_version: str) -> tuple:
    """L'endpoint della risorsa e se usare l'API v1 (un endpoint che finisce con /openai/v1 vuol dire v1)."""
    endpoint = base_url.strip().rstrip("/")
    v1 = api_version.strip().lower() == "v1"
    match = re.search(r"/openai(/v1)?$", endpoint, re.I)
    if match:
        endpoint = endpoint[:match.start()]
        v1 = v1 or bool(match.group(1))
    result = (endpoint, v1)
    return result


class AzureOpenAIProvider(Provider):
    def _ask(self, system: str, user: str, schema: dict) -> str:
        profile = self.profile
        if not profile.server or not profile.model:
            raise AIError("Il profilo Azure OpenAI richiede un endpoint e il nome del deployment")
        key = profile.api_key
        if not key:
            raise AIError(f"Nessuna chiave API per il profilo {profile.name!r}")
        endpoint, v1 = azure_endpoint(profile.server, profile.api_version)
        body = _openai_body(profile, system, user, schema)
        if v1:
            url = f"{endpoint}/openai/v1/chat/completions"
            body["model"] = profile.model
        else:
            url = f"{endpoint}/openai/deployments/{profile.model}/chat/completions?api-version={profile.api_version}"
        data = self._post("Azure OpenAI", url, body, {"api-key": key})
        result = _openai_content("Azure OpenAI", data)
        return result


class OpenAIProvider(Provider):
    def _ask(self, system: str, user: str, schema: dict) -> str:
        profile = self.profile
        if not profile.model:
            raise AIError("Il profilo OpenAI richiede il nome del modello")
        key = profile.api_key
        if not key:
            raise AIError(f"Nessuna chiave API per il profilo {profile.name!r}")
        body = _openai_body(profile, system, user, schema)
        body["model"] = profile.model
        data = self._post("OpenAI", OPENAI_URL, body, {"Authorization": f"Bearer {key}"})
        result = _openai_content("OpenAI", data)
        return result


class AnthropicProvider(Provider):
    """Claude con l'SDK ufficiale. Temperatura e thinking non si inviano: i modelli attuali rifiutano la temperatura
    e decidono da soli quanto ragionare (adaptive thinking); la profondità si regola con effort."""

    def _ask(self, system: str, user: str, schema: dict) -> str:
        import anthropic

        profile = self.profile
        if not profile.model:
            raise AIError("Il profilo Anthropic richiede il nome del modello")
        key = profile.api_key
        if not key:
            raise AIError(f"Nessuna chiave API per il profilo {profile.name!r}")
        client = anthropic.Anthropic(api_key=key, timeout=float(profile.timeout), max_retries=2)
        request = {
            "model": profile.model,
            "max_tokens": ANTHROPIC_MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"effort": ANTHROPIC_EFFORT, "format": {"type": "json_schema", "schema": schema}},
        }
        if profile.model in ANTHROPIC_FALLBACK_MODELS:
            request["betas"] = [ANTHROPIC_FALLBACK_BETA]
            request["fallbacks"] = "default"
        try:
            response = client.beta.messages.create(**request)
        except anthropic.AuthenticationError as exc:
            raise AIError("Anthropic: chiave API non valida") from exc
        except anthropic.PermissionDeniedError as exc:
            raise AIError(f"Anthropic: la chiave non ha accesso a questo modello ({exc.message})") from exc
        except anthropic.NotFoundError as exc:
            raise AIError(f"Anthropic: modello {profile.model!r} non trovato") from exc
        except anthropic.RateLimitError as exc:
            raise AIError("Anthropic: troppe richieste, riprova tra poco") from exc
        except anthropic.BadRequestError as exc:
            raise AIError(f"Anthropic: richiesta rifiutata ({exc.message})") from exc
        except anthropic.APIStatusError as exc:
            raise AIError(f"Anthropic: errore {exc.status_code} ({exc.message})") from exc
        except anthropic.APIConnectionError as exc:
            raise AIError(f"Anthropic: connessione non riuscita ({exc})") from exc
        if response.stop_reason == "refusal":
            raise AIError("Anthropic: il modello ha rifiutato la richiesta")
        if response.stop_reason == "max_tokens":
            raise AIError("Anthropic: risposta troncata (troppo lunga)")
        parts = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)
        result = "".join(parts)
        return result


def local_ollama_models(server: str = OLLAMA_LOCAL_SERVER, timeout: float = 2.0) -> list:
    """I modelli di chat installati nell'Ollama del computer: non quelli ":cloud" (girano su ollama.com, non qui) né
    quelli di sola embedding. Vuoto se Ollama non risponde."""
    try:
        response = requests.get(server.rstrip("/") + "/api/tags", timeout=timeout)
        response.raise_for_status()
        models = response.json().get("models", [])
    except (requests.RequestException, ValueError, AttributeError):
        models = []
    result = []
    for model in models:
        name = str(model.get("name", "")) if isinstance(model, dict) else ""
        lowered = name.lower()
        if name and "cloud" not in lowered and "embed" not in lowered:
            result.append(name)
    return result


def choose_local_model(installed: list) -> str:
    """Il modello predefinito della scansione: il primo installato tra le famiglie preferite, altrimenti il primo
    installato, altrimenti DEFAULT_MODELS[OLLAMA] (da scaricare con ollama pull)."""
    result = ""
    for family in PREFERRED_LOCAL_FAMILIES:
        for name in installed:
            if not result and name.lower().startswith(family):
                result = name
    if not result and installed:
        result = installed[0]
    if not result:
        result = DEFAULT_MODELS[OLLAMA]
    return result


def ensure_default_profile(home) -> bool:
    """Al primo avvio (nessun profilo salvato): il profilo "Ollama locale" su questo computer, scelto come AI della
    scansione. Le scelte già fatte non si toccano mai. True quando l'ha creato."""
    created = False
    if not (home / PROFILES_FILE).exists():
        profile = ProviderProfile(name=DEFAULT_SCAN_PROFILE, kind=OLLAMA, base_url=OLLAMA_LOCAL_SERVER,
                                  model=choose_local_model(local_ollama_models()))
        save_profiles([profile], home)
        settings = AppSettings.load(home)
        if not settings.scan_profile:
            settings.scan_profile = DEFAULT_SCAN_PROFILE
            settings.save(home)
        created = True
    return created


def make_provider(profile: ProviderProfile) -> Provider:
    if profile.kind == OLLAMA:
        result = OllamaProvider(profile)
    elif profile.kind == AZURE:
        result = AzureOpenAIProvider(profile)
    elif profile.kind == OPENAI:
        result = OpenAIProvider(profile)
    elif profile.kind == ANTHROPIC:
        result = AnthropicProvider(profile)
    else:
        raise AIError(f"Tipo di AI sconosciuto {profile.kind!r}")
    return result


def connection_test(profile: ProviderProfile) -> tuple:
    """Una richiesta vera e piccola: (riuscita, messaggio)."""
    try:
        data = make_provider(profile).ask_json(
            "You answer with a JSON object only.",
            'Reply with {"ok": true, "colour": "<the colour of a clear daytime sky, one English word>"}.',
            TEST_SCHEMA)
        good = data.get("ok") is True
        if good:
            message = f"Il modello risponde correttamente (colore: {data.get('colour', '?')})."
        else:
            message = f"Il modello ha risposto, ma non come richiesto: {data}"
    except AIError as exc:
        good = False
        message = str(exc)
    result = (good, message)
    return result
