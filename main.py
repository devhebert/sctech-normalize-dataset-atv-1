from infrastructure.initial_data_loader import load_dataset_files
from model.DatasetFiles import DatasetFiles
from service import product_service_impl
from service import order_service_impl
import service.validation.product_validation_service as product_validation_service
import service.validation.order_validation_service as order_validation_service
from infrastructure.storage import ResultSaver
from typing import List, Dict


def main() -> None:

    print("######################################################################")

    dataset: DatasetFiles = load_dataset_files();

    # produtos originais carregados (materialize iterator)
    original_products: List[Dict[str, str]] = list(dataset.products);
    print(f'Número de produtos (originais): {len(original_products)}');

    # etapa 1: limpeza (remoção de registros com dimensões físicas inválidas)
    valid_products, removed_products = product_validation_service.validate_products(original_products);
    print(f'Número de produtos (após remover inválidos): {len(valid_products)}');

    # etapa 2: normalização dos produtos já sanitizados
    normalized_products: List[Dict[str, str]] = product_service_impl.normalize_values(list(valid_products));
    print(f'Número de produtos tratados: {len(normalized_products)}');

    print("######################################################################")

    # ordens de pedidos carregados
    original_orders: List[Dict[str, str]] = list(dataset.orders);
    print(f'Nmero de pedidos (originais): {len(original_orders)}');

    # etapa 1: valida e limpa pedidos sem ids
    valid_orders, removed_orders = order_validation_service.validate_orders(original_orders);
    print(f'Nmero de pedidos (após remover invlidos): {len(valid_orders)}');

    # etapa 2: normalização das ordens já sanitizadas
    normalized_orders = order_service_impl.normalize_values(valid_orders);
    print(f'Número de pedidos tratados: {len(normalized_orders)}');

    print("######################################################################")

    # salvar resultados em versioning/clean/ usando ResultSaver (encapsula gravações e backups)
    saver = ResultSaver()

    # produtos: sanitizados e removidos
    prod_status = saver.save_products(normalized_products, removed_products)
    if prod_status.get('sanitized'):
        if prod_status['sanitized'] == 'no_change':
            print('Nenhuma alterao no arquivo de produtos; no criou backup nem sobrescreveu.');
        else:
            print(f"{prod_status['sanitized'].capitalize()} e backup salvo para produtos");
    if prod_status.get('removed'):
        if prod_status['removed'] == 'no_change':
            print('Nenhuma alterao no arquivo de removidos; no criou backup nem sobrescreveu.');
        else:
            print(f"{prod_status['removed'].capitalize()} e backup salvo para removidos");

    # orders: sanitizados e removidos
    order_status = saver.save_orders(valid_orders, removed_orders)
    if order_status.get('sanitized'):
        if order_status['sanitized'] == 'no_change':
            print('Nenhuma alterao no arquivo de orders sanitizados; no criou backup nem sobrescreveu.');
        else:
            print(f"{order_status['sanitized'].capitalize()} e backup salvo para orders sanitizados");
    if order_status.get('removed'):
        if order_status['removed'] == 'no_change':
            print('Nenhuma alterao no arquivo de orders removidos; no criou backup nem sobrescreveu.');
        else:
            print(f"{order_status['removed'].capitalize()} e backup salvo para orders removidos");


if __name__ == '__main__':
    main()