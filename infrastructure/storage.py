from pathlib import Path
from typing import List, Dict, Optional

from . import config, output

# Type aliases para deixar o código mais legível
Row = Dict[str, str]
Dataset = List[Row]


"""Armazenamento limpo de dados processados.

Este módulo define a classe `CleanStorage` responsável por gravar arquivos
sanitizados no diretório de limpeza (`clean_dir`) e gerenciar backups.
"""


class CleanStorage:
    """Gerencia gravação de arquivos sanitizados e backups.

    A classe cria o diretório `clean_dir` caso não exista e fornece métodos
    para gravar CSVs com ou sem backup. Os nomes padrão dos arquivos são
    definidos como atributos de instância.
    """
    def __init__(self, clean_dir: Optional[Path] = None):
        # diretório onde serão salvos os arquivos limpos (padrão vindo do config)
        self.clean_dir = clean_dir or config.CLEAN_DIR;
        # diretório onde serão armazenados backups
        self.backup_dir = config.BACKUP_DIR;
        # garante existência do diretório de saída
        self.clean_dir.mkdir(parents=True, exist_ok=True);

        # nomes padrão dos arquivos gerados pelo processo de limpeza
        self.products_filename = 'olist_products_sanitized.csv'
        self.removed_filename = 'olist_products_removed.csv'

    def write_csv(
            self,
            path: Path,
            rows: List[Dict[str, str]],
            fieldnames: List[str],
            encoding: str = 'utf-8',
            with_backup: bool = True,
    ) -> str:
        """Grava um CSV no caminho `path`.

        - Se `rows` estiver vazio, retorna 'no_data'.
        - Se `with_backup` for True, delega para `output.write_csv_with_backup`
          (mantendo política de backups). Caso contrário, grava diretamente
          usando `output.write_csv`.
        Retorna uma string indicando a ação: 'no_data', 'created', 'updated', ou
        'no_change' (conforme comportamento de `output`).
        """

        # se não há linhas, nada a gravar
        if not rows:
            return 'no_data';

        if with_backup:
            # grava com backup (função lida com criação de arquivo temporário,
            # comparação e backup)
            return output.write_csv_with_backup(path, rows, fieldnames, backup_dir=self.backup_dir);
        else:
            # grava diretamente no destino sem backup
            output.write_csv(path, rows, fieldnames, encoding=encoding);
            return 'created';

    def save(self, name: str, rows: List[Dict[str, str]], with_backup: bool = True) -> str:
        """Salva um conjunto de linhas sob um nome lógico.

        - `name` pode ser com ou sem extensão '.csv'.
        - Calcula os `fieldnames` a partir da primeira linha caso `rows` não
          esteja vazia.
        - Chama `write_csv` para executar a gravação real.
        """
        file_name = name if name.endswith('.csv') else f'{name}.csv';
        dest = self.clean_dir / file_name;
        # obtém o cabeçalho a partir da primeira linha quando disponível
        fieldnames = list(rows[0].keys()) if rows else [];
        return self.write_csv(dest, rows, fieldnames, with_backup=with_backup);


class ResultSaver:
    """Encapsula a gravação dos resultados de limpeza/validação.

    Fornece métodos para salvar resultados de produtos e orders (tanto os
    registros sanitizados quanto os removidos). Centraliza o flattening dos
    registros removidos e a chamada para `CleanStorage.save`.
    """
    def __init__(self, storage: Optional[CleanStorage] = None):
        self.storage = storage or CleanStorage()

    def _flatten_removed_records(self, removed: List[Dict[str, object]], key_name: str) -> List[Row]:
        """Transforma a lista de registros removidos em linhas planas para CSV.

        `key_name` é a chave que contém o registro original ('product' ou
        'order'). Adiciona colunas `_removed_reason` e `_missing_fields`.
        """
        flat: List[Row] = []
        for rec in removed:
            row = rec.get(key_name, {}) if isinstance(rec.get(key_name), dict) else {}
            # copia para evitar mutação do objeto original
            row_copy: Row = {k: str(v) for k, v in row.items()} if isinstance(row, dict) else {}
            row_copy['_removed_reason'] = rec.get('reason') or ''
            missing = rec.get('missing_fields', []) or []
            row_copy['_missing_fields'] = ';'.join(missing)
            flat.append(row_copy)
        return flat

    def save_products(self, sanitized_rows: List[Row], removed_records: List[Dict[str, object]]) -> Dict[str, Optional[str]]:
        """Salva produtos sanitizados e removidos usando `CleanStorage`.

        Retorna um dicionário com chaves 'sanitized' e 'removed' contendo os
        statuses retornados por `CleanStorage.save` (ou None se não aplicável).
        """
        result: Dict[str, Optional[str]] = {'sanitized': None, 'removed': None}
        if sanitized_rows:
            result['sanitized'] = self.storage.save('olist_products_sanitized', sanitized_rows)

        if removed_records:
            flat_rows = self._flatten_removed_records(removed_records, 'product')
            if flat_rows:
                result['removed'] = self.storage.save('olist_products_removed', flat_rows)

        return result

    def save_orders(self, sanitized_rows: List[Row], removed_records: List[Dict[str, object]]) -> Dict[str, Optional[str]]:
        """Salva orders sanitizados e removidos.

        Mesma semântica de retorno que `save_products`.
        """
        result: Dict[str, Optional[str]] = {'sanitized': None, 'removed': None}
        if sanitized_rows:
            result['sanitized'] = self.storage.save('olist_orders_sanitized', sanitized_rows)

        if removed_records:
            flat_rows = self._flatten_removed_records(removed_records, 'order')
            if flat_rows:
                result['removed'] = self.storage.save('olist_orders_removed', flat_rows)

        return result

