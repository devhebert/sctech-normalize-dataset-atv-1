import csv
import sys
from pathlib import Path
from typing import Dict, Iterator, List

from model.DatasetFiles import DatasetFiles

"""Leitor inicial de dados do dataset.

Funções auxiliares para carregar os CSVs do diretório `dataset`.
As funções retornam estruturas simples: uma lista de dicionários para
`orders` e um iterador de dicionários para `products` (streaming).
"""

LOG_ERROR = sys.stderr


def _read_csv_as_dicts(path: Path, encoding: str = 'utf-8') -> List[Dict[str, str]]:
    """Lê um CSV e retorna todos os registros como uma lista de dicionários.

    Uso indicado para arquivos menores que podem ser carregados em memória
    (por exemplo, pedidos).
    """
    with path.open('r', encoding=encoding, newline='') as order_file_dataset:
        reader = csv.DictReader(order_file_dataset)
        # retorna todos os registros como uma lista
        return [row for row in reader];


def _stream_csv_as_dicts(path: Path, encoding: str = 'utf-8') -> Iterator[Dict[str, str]]:
    """Abre um CSV e devolve um iterador de dicionários (streaming).

    Uso indicado para arquivos potencialmente grandes (por exemplo, produtos),
    evitando carregar tudo na memória. Cada chamada ao iterador retorna uma
    linha como dicionário.
    """
    with path.open('r', encoding=encoding, newline='') as product_file_dataset:
        reader = csv.DictReader(product_file_dataset)

        for row in reader:
            # produz uma linha por vez
            yield row;


def load_dataset_files() -> DatasetFiles:
    """Carrega os arquivos do dataset e retorna um `DatasetFiles`.

    - Verifica se a pasta `dataset` existe.
    - Verifica a existência dos arquivos esperados.
    - Carrega `orders` como lista e `products` como iterador.
    """
    # obtém o diretório base do projeto (dois níveis acima deste arquivo)
    base_path: Path = Path(__file__).resolve().parent.parent;
    dataset_directory: Path = base_path / 'dataset';

    if not dataset_directory.exists():
        # erro claro em português para facilitar debugging
        raise FileNotFoundError(f'Pasta dataset não encontrada: {dataset_directory}');

    orders_file: Path = dataset_directory / 'olist_orders_dataset.csv';
    products_file: Path = dataset_directory / 'olist_products_dataset.csv';

    # valida existência dos arquivos necessários
    for path in (orders_file, products_file):
        if not path.exists():
            raise FileNotFoundError(f'Arquivo não encontrado: {path}');

    # lê pedidos (carrega tudo em memória)
    order_list: List[Dict[str, str]] = _read_csv_as_dicts(orders_file);
    # produtos serão lidos em streaming
    product_list: Iterator[Dict[str, str]] = _stream_csv_as_dicts(products_file);

    dataset_files: DatasetFiles = DatasetFiles(
        orders=order_list,
        products=product_list
    );

    # retorna o container com os dados prontos para uso
    return dataset_files;
