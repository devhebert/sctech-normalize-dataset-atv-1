from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(slots=True)
class ColumnStatistic:
    """Estatísticas de média/mediana para uma única coluna numérica."""
    mean: Optional[float]
    median: Optional[float]


@dataclass(slots=True)
class ProductCategoryStatistic:
    """Estatísticas para uma categoria de produto que contém uma contagem e
    estatísticas por coluna."""
    count_total: int
    numeric_stats: Dict[str, ColumnStatistic]


@dataclass(slots=True)
class ProductCategoryStats:
    """Contêiner para estatísticas agregadas por categoria de produto.

    O atributo `categories` mapeia nome_da_categoria -> ProductCategoryStatistic.
    Cada ProductCategoryStatistic contém `count_total` e um dicionário
    `numeric_stats` que mapeia nomes de colunas numéricas para seu
    respectivo `ColumnStatistic`.
    """
    categories: Dict[str, ProductCategoryStatistic]


