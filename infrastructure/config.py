from pathlib import Path

# Diretórios base
BASE_DIR: Path = Path(__file__).resolve().parent.parent;
CLEAN_DIR: Path = BASE_DIR / 'versioning' / 'clean';
BACKUP_DIR: Path = CLEAN_DIR / 'backups';

# Política de backup
# Se True, mantém apenas um arquivo de backup por destino,
# sobrescrevendo o anterior quando houver alteração no conteúdo.
KEEP_SINGLE_BACKUP: bool = True;

# Define se deve comparar o arquivo novo com o existente
# antes de criar backups (recomendado manter True).
COMPARE_WITH_FILECMP: bool = True;

# Prefixo utilizado para arquivos temporários
# antes da movimentação atômica.
TMP_PREFIX: str = '.tmp.';