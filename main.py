import os
import zipfile
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from datetime import datetime
import tempfile


class XMLGenerator(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Gerador de XML")
        self.layout = QVBoxLayout()
        self.button = QPushButton('Carregar Ficheiro', self)
        self.button.clicked.connect(self.file_open)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        self.zip_name = None

    def file_open(self):
        name = QFileDialog.getOpenFileName(self, 'Abrir Ficheiro')[0]

        base_name = os.path.basename(name)

        if name.endswith('.zip'):
            self.zip_name = name
            self.list_zip_contents(name)
        elif name.endswith('.p21'):
            self.create_zip_with_files(name)
        else:
            print("Formato de arquivo não suportado.")

    def list_zip_contents(self, zip_name):
        with zipfile.ZipFile(zip_name, 'r') as zipf:
            zip_contents = zipf.namelist()

            # Verifica se os arquivos XML estão na raiz do ZIP
            if 'package_assortment.xml' in zip_contents and 'package_meta_data.xml' in zip_contents:
                print("Ambos os arquivos XML estão presentes na raiz do arquivo ZIP.")
                
                # Listar os arquivos encontrados no ZIP
                print("Arquivos encontrados no ZIP:")
                for file_name in zip_contents:
                    print(file_name)
                
                # Extrai e analisa o arquivo "package_assortment.xml"
                with zipf.open('package_assortment.xml') as xml_file:
                    xml_content = xml_file.read().decode('utf-8')
                    self.extract_element_values(xml_content)
            else:
                print("Um ou ambos os arquivos XML não foram encontrados na raiz do arquivo ZIP.")


    def extract_element_values(self, xml_content):
        root = ET.fromstring(xml_content)
        
        # Extrai os valores de todos os elementos
        for item in root.findall('.//item'):
            product_id = item.find('product_id').text
            p21_file_name = item.find('p21_file_name').text
            p21_file_url = item.find('p21_file_url').text
            
            # Imprime os valores extraídos
            print(f"Product ID: {product_id}")
            print(f"P21 File Name: {p21_file_name}")
            print(f"P21 File URL: {p21_file_url}")
            
            # Extrai o ZIP para um diretório temporário
            with zipfile.ZipFile(self.zip_name, 'r') as zipf:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zipf.extractall(temp_dir)
                    
                    # Constrói o caminho absoluto do arquivo
                    file_path = os.path.join(temp_dir, p21_file_url.lstrip('/'))  # Remove a barra inicial se houver
                    
                    # Verifica se o arquivo existe dentro do diretório temporário
                    if os.path.exists(file_path):
                        print(f"O arquivo {p21_file_name} existe no diretório {file_path}")
                    else:
                        print(f"O arquivo {p21_file_name} não foi encontrado no diretório {file_path}")


    def create_zip_with_files(self, p21_path):
        p21_file_name = os.path.basename(p21_path)
        p21_file_name_without_ext = os.path.splitext(p21_file_name)[0]
        zip_file_name = p21_file_name_without_ext + '.zip'

        # Cria o arquivo XML 'package_assortment.xml'
        package_assortment = Element('package_assortment')
        package_assortment.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        package_assortment.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')

        item = SubElement(package_assortment, 'item')

        product_id = SubElement(item, 'product_id')
        product_id.text = p21_file_name_without_ext

        gtc_generic_class_id = SubElement(item, 'gtc_generic_class_id')
        gtc_generic_class_id.text = 'INSI'

        gtc_vendor_class_id = SubElement(item, 'gtc_vendor_class_id')
        gtc_vendor_class_id.text = 'INSI_MISO$C'

        current_datetime = datetime.now()
        p21_value_change_timestamp = SubElement(item, 'p21_value_change_timestamp')
        p21_value_change_timestamp.text = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        p21_structure_change_timestamp = SubElement(item, 'p21_structure_change_timestamp')
        p21_structure_change_timestamp.text = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        p21_file_name_elem = SubElement(item, 'p21_file_name')
        p21_file_name_elem.text = p21_file_name_without_ext + '.p21'

        p21_file_url = SubElement(item, 'p21_file_url')
        p21_file_url.text = "product_data_files\\" + p21_file_name_without_ext + '.p21'

        gtc_generic_version = SubElement(item, 'gtc_generic_version')
        gtc_generic_version.text = "1.7"

        unit_system = SubElement(item, 'unit_system')
        unit_system.text = "metric"

        xml_str = tostring(package_assortment, encoding='UTF-8').decode('UTF-8')
        xml_file_path = os.path.join(os.path.dirname(p21_path), 'package_assortment.xml')

        with open(xml_file_path, 'w', encoding='UTF-8') as file:
            file.write(xml_str)
            print(f"Arquivo XML 'package_assortment.xml' criado com sucesso.")

        # Obtenha as informações do arquivo STEP a partir do arquivo P21
        step_info = extract_step_info_from_p21(p21_path)

        if not step_info:
            print("Nome do arquivo STEP não encontrado no arquivo P21.")
            return

        # Construa o caminho completo do arquivo STEP
        step_path = os.path.join(os.path.dirname(p21_path), step_info)

        # Cria o arquivo XML 'package_meta_data.xml' com base no arquivo P21
        package_meta_data = Element('package_meta_data')
        package_meta_data.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        package_meta_data.set('xsi:noNamespaceSchemaLocation', '../../xml schemas/package_meta_data_update20150223.xsd')

        supported_gtc_generic_versions = SubElement(package_meta_data, 'supported_gtc_generic_versions')
        supported_gtc_generic_versions.text = '1.10'

        vendor_hierarchy_version = SubElement(package_meta_data, 'vendor_hierarchy_version')
        vendor_hierarchy_version.text = '2.0.0'

        # Extraia informações do P21 para "search in p21"
        # Aqui, você deve adicionar o código para extrair as informações do P21 e preencher as tags correspondentes
        vendor_name = SubElement(package_meta_data, 'vendor_name')
        vendor_name.text = 'Kennametal'

        vendor_acronym = SubElement(package_meta_data, 'vendor_acronym')
        vendor_acronym.text = 'KMT'

        current_datetime = datetime.now()
        gtc_package_creation_date = SubElement(package_meta_data, 'gtc_package_creation_date')
        gtc_package_creation_date.text = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        gtc_package_id = SubElement(package_meta_data, 'gtc_package_id')
        gtc_package_id.text = '20230829070341'

        logo_url = SubElement(package_meta_data, 'logo_url')

        language = SubElement(package_meta_data, 'language')

        language_code = SubElement(language, 'language_code')
        language_code.text = 'eng'

        short_description = SubElement(language, 'short_description')
        short_description.text = 'editool GTC class hierarchy structure - August 2023 with a subset of product data.'

        long_description = SubElement(language, 'long_description')
        long_description.text = 'This package includes the hierarchy provided by GTC'

        disclaimer_url = SubElement(language, 'disclaimer_url')
        disclaimer_url.text = './disclaimer/en-us/disclaimer_en.txt'

        xml_str_meta = tostring(package_meta_data, encoding='UTF-8').decode('UTF-8')
        xml_file_path_meta = os.path.join(os.path.dirname(p21_path), 'package_meta_data.xml')

        with open(xml_file_path_meta, 'w', encoding='UTF-8') as file:
            file.write(xml_str_meta)
            print(f"Arquivo XML 'package_meta_data.xml' criado com sucesso.")

        # Cria o arquivo ZIP com os três arquivos
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as myzip:
            myzip.write(p21_path, os.path.join('product_data_files', p21_file_name_without_ext + '.p21'))
            myzip.write(step_path, os.path.join('product_3d_models_detailed', step_info))
            myzip.write(xml_file_path, 'package_assortment.xml')
            myzip.write(xml_file_path_meta, 'package_meta_data.xml')
            print(f"Arquivo ZIP {zip_file_name} criado com sucesso.")


def extract_step_info_from_p21(p21_path):
    step_info = None
    with open(p21_path, 'r') as p21_file:
        for line in p21_file:
            if "EXTERNAL_FILE_ID_AND_LOCATION" in line:
                parts = line.split("('")
                if len(parts) >= 2:
                    file_info = parts[1].split("',")[0].strip()
                    if file_info.endswith('.stp') or file_info.endswith('.step'):
                        step_info = file_info
                        break

    print("Nome do arquivo STEP encontrado:", step_info)
    return step_info

def main():
    app = QApplication([])
    ex = XMLGenerator()
    ex.show()
    app.exec_()

if __name__ == '__main__':
    main()
