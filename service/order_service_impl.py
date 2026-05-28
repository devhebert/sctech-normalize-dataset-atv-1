from typing import List, Dict
from datetime import datetime

"""Serviço de regras/normalização para orders.

Contém lógica de formatação temporal e de separação/contagem de pedidos com
`order_delivered_customer_date` ausente. Essas funções complementam a
validação realizada em `service/validation/order_validation_service.py`.
"""


def _format_order_approved_dates(orders: List[Dict[str, str]]) -> int:
	"""Formata a coluna `order_approved_at` para 'DD/MM/YYYY'.

	Tenta parsear com `%Y-%m-%d %H:%M:%S` e em seguida com `fromisoformat`.
	Retorna o número de campos formatados.
	"""
	formatted_count: int = 0
	for order in orders:
		raw = order.get('order_approved_at')
		if raw is None:
			continue
		if not isinstance(raw, str) or raw.strip() == '':
			continue
		s = raw.strip()
		try:
			dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
			order['order_approved_at'] = dt.strftime('%d/%m/%Y')
			formatted_count += 1
		except Exception:
			try:
				dt = datetime.fromisoformat(s)
				order['order_approved_at'] = dt.strftime('%d/%m/%Y')
				formatted_count += 1
			except Exception:
				continue
	return formatted_count


def _separate_missing_delivery_dates(orders: List[Dict[str, str]]) -> Dict[str, object]:
	"""Separa registros que têm `order_delivered_customer_date` ausente.

	Conta quantos desses têm status cancelado e retorna listas/contagens.
	"""
	missing_records: List[Dict[str, str]] = []
	missing_and_canceled: List[Dict[str, str]] = []
	missing_and_not_canceled: List[Dict[str, str]] = []

	for order in orders:
		val = order.get('order_delivered_customer_date')
		if val is None or (isinstance(val, str) and val.strip() == ''):
			missing_records.append(order)
			status = (order.get('order_status') or '').strip().lower()
			if status in ('canceled', 'cancelled'):
				missing_and_canceled.append(order)
			else:
				missing_and_not_canceled.append(order)

	return {
		'total_missing': len(missing_records),
		'missing_canceled': len(missing_and_canceled),
		'missing_not_canceled': len(missing_and_not_canceled),
		'missing_records': missing_records,
		'missing_not_canceled_records': missing_and_not_canceled,
	}


def _rules_executor(orders: List[Dict[str, str]]) -> None:
	formatted = _format_order_approved_dates(orders)
	print(f'Datas de aprovação formatadas: {formatted}')

	separation = _separate_missing_delivery_dates(orders)
	print(f'Total de pedidos com order_delivered_customer_date ausente: {separation["total_missing"]}')
	print(f'Desses, com status cancelado: {separation["missing_canceled"]}')
	print(f'Desses, sem status cancelado: {separation["missing_not_canceled"]}')


def normalize_values(orders: List[Dict[str, str]]) -> List[Dict[str, str]]:

	"""Normaliza os valores da lista de pedidos.

	Esta função aplica regras/normalizações nos dicionários de `orders`.
	As modificações são feitas in-place (nos próprios dicionários) e a mesma
	lista é retornada por conveniência.

	Regras aplicadas (delegadas a `_rules_executor`):
	- Formatação de `order_approved_at` para 'DD/MM/YYYY' quando possível.
	- Separação e contagem de pedidos com `order_delivered_customer_date` ausente
	  e classificação por status cancelado/não cancelado.
	"""

	# Chama o executor de regras passando a lista de pedidos.
	# `_rules_executor` realiza as mudanças em-place na estrutura fornecida.
	_rules_executor(orders)

	# Retorna a lista (modificada) para facilitar encadeamento/uso pelo chamador.
	return orders



