import csv
import os
import re


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def collect_files():
    data_dir = os.path.join(CURRENT_DIR, "data")
    source_files = [f"data/{i}" for i in os.listdir(data_dir) if i.split('.')[1] == 'txt']

    return source_files


def get_data():
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    data = collect_files()
    main_data = [["Изготовитель системы", "Название ОС", "Код продукта", "Тип системы"]]

    for el in data:
        result = []
        with open(el, "r", encoding="windows-1251") as f:
            for line in f.readlines():
                result += re.findall(r'^(\w[^:]+).*:\s+([^:\n]+)\s*$', line)

            for el in result:
                os_prod_list.append(el[1]) if el[0] == main_data[0][0] else None
                os_name_list.append(el[1]) if el[0] == main_data[0][1] else None
                os_code_list.append(el[1]) if el[0] == main_data[0][2] else None
                os_type_list.append(el[1]) if el[0] == main_data[0][3] else None

    for i in range(len(os_prod_list)):
        main_data.append([os_prod_list[i], os_name_list[i], os_code_list[i], os_type_list[i]])
                
    return main_data


def write_to_csv(filename: str):
    data = get_data()
    filepath = os.path.join(CURRENT_DIR, "data", filename)

    with open(filepath, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

        for line in data:
            writer.writerow(line)

    print(f'Данные сохранены в {filepath}')


if __name__ == "__main__":
    write_to_csv("main_data.csv")