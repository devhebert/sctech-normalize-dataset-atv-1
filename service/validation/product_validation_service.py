from typing import Optional

from model.enum.ProductColumn import ProductColumn


"""Serviços de validação para os registros de produtos.

O módulo verifica se as colunas físicas obrigatórias (peso e dimensões)
estão presentes e válidas; registros com dimensões inválidas são separados
em uma lista de removidos com motivo e campos faltantes.
"""


def _safe_parse_numeric(value: Optional[str], dtype: str) -> Optional[float]:
    """Tenta converter `value` em float de forma segura.

    Aceita valores numéricos int/float ou strings numéricas (com vírgula ou
    ponto). Retorna None para valores vazios ou 'NA'. Mantém comportamento
    original, apenas documenta e aceita Optional[str] porque o código já
    trata None.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    # remove espaços em torno e trata strings vazias/NA
    string_value = str(value).strip()
    if string_value == '' or string_value.upper() == 'NA':
        return None

    # aceita vírgula como separador decimal
    string_value = string_value.replace(',', '.')
    try:
        return float(string_value)
    except ValueError:
        return None


def validate_products(products: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    """Valida a presença/validade das dimensões físicas dos produtos.

    Percorre os produtos e verifica as colunas de peso e dimensões físicas
    (peso, comprimento, altura, largura). Se alguma dessas colunas não puder
    ser interpretada como número, o produto é movido para `removed_record_list`
    com o motivo `missing_or_invalid_physical_dimensions` e a lista de campos
    faltantes. Caso contrário, o produto é incluído em `sanitized_list`.

    Retorna uma tupla: (sanitized_list, removed_record_list).
    """
    # colunas físicas obrigatórias esperadas no CSV
    physical_columns = [
        ProductColumn.PRODUCT_WEIGHT_G.value,
        ProductColumn.PRODUCT_LENGTH_CM.value,
        ProductColumn.PRODUCT_HEIGHT_CM.value,
        ProductColumn.PRODUCT_WIDTH_CM.value,
    ]

    sanitized_list: list[dict[str, str]] = []
    removed_record_list: list[dict[str, object]] = []

    for product in products:
        missing_list: list[str] = []
        for column in physical_columns:
            # obtém o valor da coluna (string ou '' se ausente)
            value = product.get(column, '')
            num = _safe_parse_numeric(value, 'float')
            if num is None:
                # marca coluna como faltante/inválida
                missing_list.append(column)

        if missing_list:
            # registra o produto removido com detalhes para auditoria
            removed_record_list.append({
                'product': dict(product),
                'missing_fields': missing_list,
                'reason': 'missing_or_invalid_physical_dimensions'
            })
            continue

        # produto validado com sucesso
        sanitized_list.append(product)

    return sanitized_list, removed_record_list
