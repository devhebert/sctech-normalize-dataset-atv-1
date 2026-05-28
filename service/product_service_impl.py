import re
from statistics import mean, median, StatisticsError
from typing import Optional, Dict, List, cast

from model.ProductCategoryStats import (
    ProductCategoryStats,
    ProductCategoryStatistic,
    ColumnStatistic,
)
from model.enum.ProductColumn import ProductColumn

"""Serviços utilitários para normalização e agregação de dados de produtos."""


def _normalize_string(value: str) -> str:
    """Normaliza uma string removendo espaços e caracteres não alfanuméricos.

    Retorna uma string minúscula e sem pontuação. Se `value` for None,
    retorna string vazia.
    """
    if value is None:
        return '';

    string_value: str = value.strip().lower();
    # remove caracteres que não sejam letras, números ou espaços
    string_value = re.sub(r"[^\w\s]", "", string_value);
    # normaliza múltiplos espaços para um único espaço
    string_value = re.sub(r"\s+", " ", string_value);

    return string_value;


def _safe_parse_numeric(value: Optional[str], dtype: str) -> Optional[float]:
    """Tenta converter `value` para float de forma segura.

    Aceita `int`, `float` ou strings numéricas (com vírgula ou ponto). Valores
    vazios ou 'NA' retornam None.
    """
    if value is None:
        return None;

    if isinstance(value, (int, float)):
        return float(value);

    string_value: str = str(value).strip();
    if string_value == '' or string_value.upper() == 'NA':
        return None;

    # permite números com vírgula como separador decimal
    string_value = string_value.replace(',', '.');
    try:
        return float(string_value);
    except ValueError:
        return None;


def _apply_product_value_formatting_rule_to_products(products: List[Dict[str, str]]) -> int:
    """Aplica regras de formatação por coluna conforme `ProductColumn`.

    - Strings são normalizadas com `_normalize_string`.
    - Valores numéricos são parseados com `_safe_parse_numeric` e formatados em
      string (inteiro ou float) para armazenamento uniforme.
    Retorna o número total de campos ajustados.
    """
    adjusted_fields_count: int = 0;
    for product in products:
        # iteramos sobre uma cópia dos itens para permitir mutação segura
        for key, value in list(product.items()):
            original_value = value;
            normalized_value: str = '';
            # procura a coluna correspondente em ProductColumn
            for column in ProductColumn:
                if column.value == key:
                    dtype = getattr(column, 'dtype', None)
                    if dtype == 'string':
                        normalized_value = _normalize_string(value)
                    elif dtype in ('int', 'float'):
                        number = _safe_parse_numeric(value, dtype)
                        if number is None:
                            normalized_value = ''
                        elif dtype == 'int':
                            normalized_value = str(int(number))
                        else:
                            normalized_value = str(number)
                    break
            else:
                # coluna desconhecida -> apenas strip para strings
                if isinstance(value, str):
                    normalized_value = value.strip()
                else:
                    normalized_value = '' if value is None else str(value)
            if str(original_value) != normalized_value:
                adjusted_fields_count += 1
            product[key] = normalized_value
    return adjusted_fields_count;


def _apply_product_category_name_rule_to_products(products: List[Dict[str, str]]) -> int:
    """Garante que todo produto possua um nome de categoria.

    Se a categoria estiver ausente ou vazia, define como 'Sem Categoria' e
    conta quantas linhas foram ajustadas.
    """
    adjusted_rows_count: int = 0;
    product_category_name: str = ProductColumn.PRODUCT_CATEGORY_NAME.value
    for product in products:
        if product_category_name not in product or not product.get(product_category_name):
            product[product_category_name] = 'Sem Categoria'
            adjusted_rows_count += 1

    return adjusted_rows_count;


def _rules_executor(
    products: List[Dict[str, str]],
    stats: Optional[ProductCategoryStats] = None,
    strategy: str = 'median',
) -> None:

    """Executa todas as regras de normalização em sequência.

    Esta função aplica: formatação de valores, preenchimento de categoria, e
    preenchimento de valores numéricos faltantes (se `stats` fornecido).
    """
    count_item_formated: int = 0;

    # Formata os valores conforme os tipos esperados
    count_item_formated = _apply_product_value_formatting_rule_to_products(products)
    print(f'Campos ajustados na formatação de valores: {count_item_formated}')

    # Garante que categoria exista
    count_item_formated = _apply_product_category_name_rule_to_products(products)
    print(f'Produtos com categoria ajustada para "Sem Categoria": {count_item_formated}')

    # Se tivermos estatísticas por categoria, preenche valores numéricos faltantes
    if stats is not None:
        abroba = _apply_missing_numeric_value_rule_to_products_using_median_or_zero(products, stats, strategy=strategy)
        print(
            f'Produtos com valores numéricos faltantes ajustados usando {strategy}: '
            f'{abroba["adjusted_fields"]} campos em {abroba["adjusted_rows"]} produtos (fallback zero: {abroba["fallback_zero_count"]})'
        )



def normalize_values(products: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Função pública para normalizar a lista de produtos.

    - Calcula estatísticas por categoria
    - Executa as regras de normalização
    Retorna a própria lista `products` (mutada) para compatibilidade com o
    código existente.
    """
    stats: ProductCategoryStats = aggregate_category_statistics(products)

    _rules_executor(products=products, stats=stats, strategy='median')

    return products;


def _apply_missing_numeric_value_rule_to_products_using_median_or_zero(
    products: List[Dict[str, str]],
    stats: ProductCategoryStats,
    strategy: str = 'median',
) -> Dict[str, int]:

    """Preenche valores numéricos faltantes por categoria.

    Para cada produto e cada coluna numérica:
    - se o valor estiver faltando, tenta pegar a média/mediana da categoria
      (conforme `strategy`).
    - se a estatística da coluna também estiver ausente, usa 0 como fallback
      e conta esse fallback.
    Retorna um dicionário com contagens de linhas/campos ajustados e fallback.
    """
    if strategy not in ('mean', 'median'):
        raise ValueError("strategy must be 'mean' or 'median'")

    adjusted_fields_count: int = 0;
    adjusted_rows_count: int = 0;
    fallback_zero_count: int = 0;

    category_key: str = ProductColumn.PRODUCT_CATEGORY_NAME.value

    numeric_columns: List[tuple[str, str]] = []

    for column in ProductColumn:
        if getattr(column, 'dtype', None) in ('int', 'float'):
            numeric_columns.append((column.value, getattr(column, 'dtype')))

    for product in products:
        row_changed: bool = False;
        category_name: str = product.get(category_key) or 'Sem Categoria'
        cat_stats: Optional[ProductCategoryStatistic] = stats.categories.get(category_name)
        if not cat_stats:
            continue
        for col_name, dtype in numeric_columns:
            raw = product.get(col_name)
            if raw is None or (
                isinstance(raw, str)
                and raw.strip() == ''
            ):
                col_stat: Optional[ColumnStatistic] = cat_stats.numeric_stats.get(col_name)
                if not col_stat:
                    continue
                # obtém a estatística (pode ser None)
                value = getattr(col_stat, strategy, None)
                # assegura que `v` é float antes de chamar round/int (evita avisos de tipo)
                if value is None:
                    fallback_zero_count += 1
                    v: float = 0.0
                else:
                    v = float(cast(float, value))
                if dtype == 'int':
                    try:
                        product[col_name] = str(int(round(v)))
                    except Exception:
                        product[col_name] = str(int(v))
                else:
                    product[col_name] = str(float(round(v, 6)))
                adjusted_fields_count += 1
                row_changed = True
        if row_changed:
            adjusted_rows_count += 1

    return {
        'adjusted_rows': adjusted_rows_count,
        'adjusted_fields': adjusted_fields_count,
        'fallback_zero_count': fallback_zero_count,
    }


def aggregate_category_statistics(products: List[Dict[str, str]]) -> ProductCategoryStats:
    """Agrupa e calcula estatísticas numéricas por categoria de produto.

    Para cada categoria calcula-se média e mediana por coluna numérica. Retorna
    um `ProductCategoryStats` contendo `ProductCategoryStatistic` por categoria.
    """

    category_key: str = ProductColumn.PRODUCT_CATEGORY_NAME.value

    numeric_columns: List[tuple[str, str]] = []  # list of (column_name, dtype)
    for col in ProductColumn:
        if getattr(col, 'dtype', None) in ('int', 'float'):
            numeric_columns.append((col.value, getattr(col, 'dtype')))

    if not numeric_columns:
        return ProductCategoryStats(categories={})

    # estrutura temporária: category -> (column -> list de valores)
    values_by_category: Dict[str, Dict[str, List[float]]] = {}
    counts_by_category: Dict[str, int] = {}

    for product in products:
        category_name: str = product.get(category_key) or 'Sem Categoria'

        # contabiliza ocorrência de produto por categoria
        counts_by_category[category_name] = counts_by_category.get(category_name, 0) + 1

        values_by_category.setdefault(category_name, {})
        for col_name, dtype in numeric_columns:
            values_by_category[category_name].setdefault(col_name, [])
            raw_value = product.get(col_name)
            numeric_value = _safe_parse_numeric(raw_value, dtype or 'float')
            if numeric_value is not None:
                values_by_category[category_name][col_name].append(numeric_value)

    categories: Dict[str, ProductCategoryStatistic] = {}

    for category_name, col_values_map in values_by_category.items():
        numeric_stats: Dict[str, ColumnStatistic] = {}
        for col_name, values in col_values_map.items():
            avg: Optional[float] = None
            med: Optional[float] = None
            try:
                if values:
                    avg = float(mean(values))
                    med = float(median(values))
            except StatisticsError:
                avg = None
                med = None

            numeric_stats[col_name] = ColumnStatistic(
                mean=round(avg, 6) if avg is not None else None,
                median=round(med, 6) if med is not None else None,
            )

        # garante presença de todas as colunas numéricas, mesmo sem valores
        for col_name, _dtype in numeric_columns:
            if col_name not in numeric_stats:
                numeric_stats[col_name] = ColumnStatistic(mean=None, median=None)

        categories[category_name] = ProductCategoryStatistic(
            count_total=counts_by_category.get(category_name, 0),
            numeric_stats=numeric_stats,
        )

    # assegura que categorias contadas mas sem valores numéricos existam no resultado
    for category_name, count in counts_by_category.items():
        if category_name not in categories:
            # cria numeric_stats vazio para todas as colunas numéricas
            numeric_stats = {col_name: ColumnStatistic(mean=None, median=None) for col_name, _ in numeric_columns}
            categories[category_name] = ProductCategoryStatistic(
                count_total=count,
                numeric_stats=numeric_stats,
            )

    return ProductCategoryStats(categories=categories)