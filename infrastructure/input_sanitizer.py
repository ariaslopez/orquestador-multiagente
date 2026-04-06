"""InputSanitizer — protección contra prompt injection y entradas maliciosas."""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class SanitizationResult:
    is_safe: bool
    sanitized_input: str
    risk_level: str          # 'safe' | 'low' | 'medium' | 'high' | 'critical'
    violations: list[str]
    original_length: int
    sanitized_length: int


class InputSanitizer:
    """
    Tres capas de protección contra prompt injection:
    1. Patrones de jailbreak conocidos
    2. Instrucciones de override de sistema
    3. Inyección estructural (delimitadores, roles falsos)
    """

    MAX_INPUT_LENGTH = int(8000)

    # Capa 1: patrones de jailbreak directos
    JAILBREAK_PATTERNS = [
        r'ignore\s+(previous|all|prior|above)\s+instructions?',
        r'disregard\s+(previous|all|prior|above|your)',
        r'forget\s+(everything|all|previous|your\s+instructions)',
        r'you\s+are\s+now\s+(a|an|the)\s+',
        r'act\s+as\s+(if\s+you\s+(are|were)|a|an)',
        r'pretend\s+(you\s+are|to\s+be)',
        r'roleplay\s+as',
        r'jailbreak',
        r'dan\s+mode',
        r'do\s+anything\s+now',
        r'ignore\s+safety',
        r'bypass\s+(safety|filter|restriction|guardrail)',
    ]

    # Capa 2: override de instrucciones de sistema
    SYSTEM_OVERRIDE_PATTERNS = [
        r'system\s*:\s*',
        r'<\s*system\s*>',
        r'\[\s*system\s*\]',
        r'new\s+instructions?\s*:',
        r'updated?\s+instructions?\s*:',
        r'override\s*:',
        r'admin\s+mode',
        r'developer\s+mode',
        r'god\s+mode',
    ]

    # Capa 3: inyección estructural
    STRUCTURAL_PATTERNS = [
        r'```\s*(system|instructions?|prompt)',
        r'---+\s*(system|instructions?|end)',
        r'\[INST\]',
        r'<\|\s*(system|user|assistant|im_start|im_end)\s*\|>',
        r'#{3,}\s*(system|instructions?)',
        r'Human\s*:\s*.{0,50}\nAssistant\s*:',  # simular turno de conversación
    ]

    def __init__(self):
        self._jailbreak_re = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.JAILBREAK_PATTERNS
        ]
        self._override_re = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.SYSTEM_OVERRIDE_PATTERNS
        ]
        self._structural_re = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.STRUCTURAL_PATTERNS
        ]

    def sanitize(self, user_input: str) -> SanitizationResult:
        """Evalua y limpia el input del usuario."""
        violations = []
        original_length = len(user_input)
        sanitized = user_input

        # Limite de longitud
        if len(sanitized) > self.MAX_INPUT_LENGTH:
            sanitized = sanitized[:self.MAX_INPUT_LENGTH]
            violations.append(f'Input truncado a {self.MAX_INPUT_LENGTH} chars')

        # Capa 1: jailbreak
        for pattern in self._jailbreak_re:
            if pattern.search(sanitized):
                violations.append(f'Jailbreak pattern: {pattern.pattern[:40]}')

        # Capa 2: system override
        for pattern in self._override_re:
            if pattern.search(sanitized):
                violations.append(f'System override pattern: {pattern.pattern[:40]}')

        # Capa 3: structural injection
        for pattern in self._structural_re:
            if pattern.search(sanitized):
                violations.append(f'Structural injection: {pattern.pattern[:40]}')

        # Calcular nivel de riesgo
        n = len(violations)
        if n == 0:
            risk = 'safe'
        elif n == 1 and 'truncado' in violations[0]:
            risk = 'low'
        elif n <= 2:
            risk = 'medium'
        elif n <= 4:
            risk = 'high'
        else:
            risk = 'critical'

        is_safe = risk in ('safe', 'low')

        return SanitizationResult(
            is_safe=is_safe,
            sanitized_input=sanitized,
            risk_level=risk,
            violations=violations,
            original_length=original_length,
            sanitized_length=len(sanitized),
        )

    def assert_safe(self, user_input: str) -> str:
        """
        Valida el input y retorna el texto limpio.
        Lanza ValueError si el riesgo es high o critical.
        """
        result = self.sanitize(user_input)
        if not result.is_safe:
            raise ValueError(
                f'Input rechazado (risk={result.risk_level}): '
                + ' | '.join(result.violations)
            )
        return result.sanitized_input
