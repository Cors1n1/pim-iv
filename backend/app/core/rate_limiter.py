import time
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, status


class InMemoryRateLimiter:
    """
    Controlador de taxa de tentativas de login em memória.
    Rastreia falhas consecutivas por IP e por conta de usuário para evitar abusos.
    
    Regra padrão:
    - 5 falhas consecutivas em menos de 120s geram bloqueio temporário de 300s.
    - Responde com HTTP 429 Too Many Requests e cabeçalho Retry-After.
    - O sucesso na autenticação limpa o histórico de falhas daquela chave.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 120, block_duration_seconds: int = 300) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_duration = block_duration_seconds
        # Estrutura: key -> (tentativas: int, primeiro_erro: float, bloqueado_ate: float)
        self._records: Dict[str, Tuple[int, float, float]] = {}

    def _clean_expired(self, now: float) -> None:
        """Limpa entradas expiradas para evitar crescimento de memória."""
        if len(self._records) > 5000:
            keys_to_delete = [
                k for k, v in self._records.items()
                if now > max(v[1] + self.window_seconds, v[2])
            ]
            for k in keys_to_delete:
                self._records.pop(k, None)

    def check_limit(self, key: str) -> None:
        """
        Verifica se a chave (IP ou e-mail) está atualmente em período de bloqueio temporário.
        Se estiver, lança HTTPException 429 com cabeçalho Retry-After.
        """
        now = time.time()
        self._clean_expired(now)

        record = self._records.get(key)
        if not record:
            return

        attempts, first_time, blocked_until = record
        if blocked_until > now:
            remaining = int(blocked_until - now)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Muitas tentativas incorretas consecutivas. Acesso temporariamente suspenso por motivos de segurança. Tente novamente em {remaining} segundos.",
                headers={"Retry-After": str(max(1, remaining))}
            )

    def record_failure(self, key: str) -> int:
        """
        Registra uma falha de autenticação.
        Retorna o total de tentativas acumuladas no ciclo.
        Se atingir max_attempts, ativa o bloqueio por block_duration.
        """
        now = time.time()
        record = self._records.get(key)

        if not record:
            self._records[key] = (1, now, 0.0)
            return 1

        attempts, first_time, blocked_until = record

        # Se já expirou a janela sem estourar o limite, reinicia ciclo
        if now - first_time > self.window_seconds and blocked_until <= now:
            self._records[key] = (1, now, 0.0)
            return 1

        new_attempts = attempts + 1
        if new_attempts >= self.max_attempts:
            new_blocked_until = now + self.block_duration
            self._records[key] = (new_attempts, first_time, new_blocked_until)
            remaining = int(self.block_duration)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de tentativas excedido (5 erros em menos de 2 minutos). Acesso bloqueado por {remaining} segundos para prevenção contra força bruta.",
                headers={"Retry-After": str(remaining)}
            )
        else:
            self._records[key] = (new_attempts, first_time, 0.0)
            return new_attempts

    def record_success(self, key: str) -> None:
        """Limpa o contador após autenticação com sucesso."""
        self._records.pop(key, None)

    def reset_all(self) -> None:
        """Reseta toda a memória (útil para testes unitários)."""
        self._records.clear()


# Instância global singleton do rate limiter de autenticação
auth_rate_limiter = InMemoryRateLimiter(
    max_attempts=5,
    window_seconds=120,
    block_duration_seconds=300
)
