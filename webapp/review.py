"""Revisão das datas da entrada e orientação de falhas, sem evidência inventada."""

from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from threading import Lock

import etl
from weekly_ranking import select_week

REVIEW_LOCK = Lock()


def review_input(path: Path, reference: date) -> dict:
    # Uma validação pesada por processo de API. A espera não bloqueia a saúde
    # ou o acompanhamento de análises, e não mantém vários CSVs lidos em RAM.
    with REVIEW_LOCK:
        rows, _encoding = etl.read_economatica(path)
        if not rows:
            raise etl.InputError('O CSV não contém linhas de dados')
        return review_week(rows, reference)


def review_week(rows: list[dict], reference: date) -> dict:
    # Usa o mesmo tratamento, em lotes para não manter toda a base normalizada
    # em RAM na API. Apenas contagens por data são somadas. A revisão não valida
    # duplicatas entre lotes, qualidade das pontas ou classificação B3:
    # essas verificações continuam obrigatórias no pipeline completo do worker.
    counts = Counter()
    for offset in range(0, len(rows), 2000):
        _records, _issues, summary = etl.transform(
            rows[offset:offset + 2000], reference, {}, Decimal('0.25'))
        for item in summary['dates']:
            counts[item['date']] += item['positive_close']
    return select_week([(date.fromisoformat(day), count) for day, count in counts.items()],
                       reference, allow_nonfriday_end=True)


def problem(message: str) -> dict:
    lower = message.lower()
    if 'cobertura insuficiente' in lower:
        code, guidance = 'coverage', 'Exporte novamente a base com cobertura comparável nas datas indicadas. A aceitação de semana encurtada não dispensa esse controle.'
    elif any(word in lower for word in ('faltam cotações', 'só há um dia', 'está distante')):
        code, guidance = 'dates', 'Confira a referência e inclua fechamentos anteriores à semana e pelo menos dois dias com preços dentro dela. Não preencha lacunas manualmente.'
    elif any(word in lower for word in ('esquema', 'cabeçalho', 'codificação', 'csv vazio', 'linhas de dados')):
        code, guidance = 'format', 'Exporte o CSV com as nove colunas documentadas, na mesma ordem, separador vírgula, datas AAAA-MM-DD e UTF-8 ou Windows-1252. Consulte Dados e tratamento.'
    elif 'ações elegíveis; são necessárias' in lower:
        code, guidance = 'universe', 'A base precisa conter pelo menos 20 ações ON/PN com preços válidos e confirmação oficial nas duas pontas. Amplie a extração sem mudar a definição de ação.'
    elif any(word in lower for word in ('classifica', 'evidência', 'universo', 'b3', 'pendente')):
        code, guidance = 'classification', 'A confirmação oficial das ações está incompleta ou conflitante. Se as fontes B3 estiverem indisponíveis, tente novamente mais tarde. Uma pendência persistente exige revisão das evidências; aceitar a semana não libera esse controle.'
    elif any(word in lower for word in ('preço', 'fechamento', 'duplicad')):
        code, guidance = 'prices', 'Confira as linhas e datas indicadas na extração original. Exporte novamente os dados corretos; o processo não corrige preços nem escolhe uma duplicata silenciosamente.'
    elif 'dez minutos' in lower:
        code, guidance = 'timeout', 'Tente novamente mais tarde ou exporte menos histórico mantendo as datas e o universo necessários à comparação.'
    else:
        code, guidance = 'processing', 'Confira o motivo, o formato e a referência antes de reenviar. Se a falha persistir, informe ao responsável o link desta execução.'
    return {'code': code, 'message': message, 'guidance': guidance}
