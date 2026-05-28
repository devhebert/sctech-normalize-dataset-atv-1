from pathlib import Path
import shutil
import filecmp
import csv
from typing import List, Dict

from . import config


"""Funções utilitárias para escrita de CSVs e criação de backups.

Este módulo fornece helpers para gravar CSVs de forma segura, criando um
arquivo temporário, comparando com o existente e mantendo backups conforme
configurações.
"""


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str], encoding: str = 'utf-8') -> None:
    """Escreve uma lista de dicionários para um arquivo CSV.

    - Garante que o diretório pai exista.
    - Usa csv.DictWriter para escrever o cabeçalho e as linhas.
    """
    # garante que o diretório de destino exista
    path.parent.mkdir(parents=True, exist_ok=True);
    # abre o arquivo em modo escrita com o encoding informado
    with path.open('w', encoding=encoding, newline='') as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames);
        # escreve o cabeçalho
        writer.writeheader();
        # escreve cada linha do CSV
        for row in rows:
            writer.writerow(row);


def write_csv_with_backup(
    dest: Path,
    rows: List[Dict[str, str]],
    fieldnames: List[str],
    backup_dir: Path = config.BACKUP_DIR,
    compare: bool = config.COMPARE_WITH_FILECMP,
    keep_single_backup: bool = config.KEEP_SINGLE_BACKUP,
    tmp_prefix: str = config.TMP_PREFIX,
) -> str:
    """Escreve CSV com estratégia de backup/atualização segura.

    Fluxo:
    1. Cria diretórios de destino e backup se necessários.
    2. Escreve os dados em um arquivo temporário (prefixado).
    3. Se o arquivo de destino já existir e `compare` for True, compara os
       arquivos usando filecmp; se idênticos, remove o temporário e retorna
       'no_change'.
    4. Se o arquivo existir e for necessário manter backup, copia o destino
       para a pasta de backup.
    5. Move o arquivo temporário para o destino final.
    6. Retorna 'created' se o arquivo não existia antes, caso contrário 'updated'.
    """

    # garante diretórios necessários
    dest.parent.mkdir(parents=True, exist_ok=True);
    backup_dir.mkdir(parents=True, exist_ok=True);

    # escreve em um arquivo temporário ao lado do destino
    tmp = dest.parent / f'{tmp_prefix}{dest.name}'
    write_csv(tmp, rows, fieldnames)

    # se solicitado, compara o arquivo temporário com o existente
    if dest.exists() and compare:
        try:
            same = filecmp.cmp(tmp, dest, shallow=False)
        except Exception:
            # em caso de erro na comparação, assume que não são iguais
            same = False
        if same:
            # não houve mudança: remove temporário e retorna status
            tmp.unlink()
            return 'no_change'

    # cria backup do arquivo existente se necessário
    if dest.exists() and keep_single_backup:
        backup_path = backup_dir / f'{dest.stem}_backup{dest.suffix}'
        shutil.copy2(dest, backup_path)
    elif dest.exists():
        # comportamento atual: também copia para backup (mantém compatibilidade)
        backup_path = backup_dir / f'{dest.stem}_backup{dest.suffix}'
        shutil.copy2(dest, backup_path)

    # substitui o arquivo de destino pelo temporário
    shutil.move(str(tmp), str(dest))

    # se o arquivo não existia antes, foi criado; caso contrário, atualizado
    return 'created' if not dest.exists() else 'updated'

