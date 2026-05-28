from enum import Enum

"""Definição das colunas do dataset de produtos.

Cada membro de `ProductColumn` guarda dois atributos:
- o `value` (nome da coluna no CSV) e
- `dtype` (tipo esperado: 'string', 'int' ou 'float').

Observação: mantivemos os nomes das colunas exatamente como no dataset
originais (não corrigimos eventuais erros de digitação nas chaves) para
preservar compatibilidade com o restante do código.
"""


class ProductColumn(Enum):
    """Enumeração com metadados de colunas de produto.

    Implementamos um __new__ personalizado para anexar o atributo `dtype`
    a cada membro. O `value` do Enum é definido como o nome da coluna usado
    nos CSVs, e `dtype` descreve o tipo de dado esperado para essa coluna.
    """
    def __new__(cls, column_name: str, dtype: str):
        # cria a instância do Enum e define o valor (nome da coluna)
        obj = object.__new__(cls)
        obj._value_ = column_name
        # armazena o tipo de dado esperado para esta coluna
        obj.dtype = dtype
        return obj

    # membros da enumeração: (nome_da_coluna_no_csv, tipo)
    PRODUCT_ID = ('product_id', 'string')
    PRODUCT_CATEGORY_NAME = ('product_category_name', 'string')
    PRODUCT_NAME_LENGTH = ('product_name_lenght', 'int')
    PRODUCT_DESCRIPTION_LENGTH = ('product_description_lenght', 'int')
    PRODUCT_PHOTOS_QTY = ('product_photos_qty', 'int')
    PRODUCT_WEIGHT_G = ('product_weight_g', 'float')
    PRODUCT_LENGTH_CM = ('product_length_cm', 'float')
    PRODUCT_HEIGHT_CM = ('product_height_cm', 'float')
    PRODUCT_WIDTH_CM = ('product_width_cm', 'float');
