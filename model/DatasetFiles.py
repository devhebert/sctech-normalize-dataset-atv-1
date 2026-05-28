from dataclasses import dataclass
from typing import Dict, Iterator, List

"""Módulo com estruturas para representar arquivos/dados do dataset.

A classe `DatasetFiles` agrupa os dados carregados dos arquivos do projeto.
"""


@dataclass(slots=True)
class DatasetFiles:
    """Contêiner para os arquivos/dados do dataset.

    Atributos:
    - orders: lista de dicionários representando registros de pedidos.
    - products: iterador de dicionários representando registros de produtos
      (é um iterador para permitir streaming de arquivos grandes sem carregar
      tudo em memória).
    """
    orders: List[Dict[str, str]]
    products: Iterator[Dict[str, str]]
    
