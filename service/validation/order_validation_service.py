from typing import Optional, List, Dict


"""Serviços de validação para registros de pedidos (orders).

Esta unidade tem o papel exclusivo de validar e remover pedidos com
`order_id` ou `customer_id` ausentes (None ou strings vazias). Regras de
normalização ou análise.
"""


def _is_missing(value: Optional[str]) -> bool:
    """Retorna True se `value` for considerado ausente/nulo."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == '':
        return True
    return False


def validate_orders(orders: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], List[Dict[str, object]]]:
    """Valida a lista de pedidos.

    Remove pedidos cujo `order_id` ou `customer_id` estejam ausentes (None ou
    strings vazias). Retorna uma tupla (valid_orders, removed_records), onde
    `removed_records` contém dicionários com o pedido original, campos
    faltantes e o motivo para remoção.
    """
    valid_orders: List[Dict[str, str]] = []
    removed_records: List[Dict[str, object]] = []

    for order in orders:
        missing_fields: List[str] = []
        # checa os campos obrigatórios
        if _is_missing(order.get('order_id')):
            missing_fields.append('order_id')
        if _is_missing(order.get('customer_id')):
            missing_fields.append('customer_id')

        if missing_fields:
            # registra o pedido removido com detalhes para auditoria
            removed_records.append({
                'order': dict(order),
                'missing_fields': missing_fields,
                'reason': 'missing_order_or_customer_id'
            })
            continue

        # pedido válido
        valid_orders.append(order)

    return valid_orders, removed_records

