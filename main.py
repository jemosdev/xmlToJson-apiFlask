import xmltodict
import xml.etree.ElementTree as ET
from flask import Flask, render_template, redirect, url_for, request, jsonify


app = Flask(__name__)


@app.route('/')
def index():
    response= render_template('index.html')
    return response


@app.errorhandler(404)
def not_found(error):
    #return render_template('404.html', error= error)
    return redirect(url_for('index'))


@app.route('/cargar-archivo', methods= ['GET','POST'])
def cargar_archivo():
    if (request.method == "GET"):
        return render_template('loadingFile.html')
    
    #verify that the file has been uploaded
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se ha proporcionado ningún archivo'})
    
    archivo = request.files['archivo']

    #verify that the file has an XML extension
    if archivo.filename == "":
        return jsonify({'error': 'El archivo no tiene nombre'})                
    else:
        if archivo and archivo.filename.endswith('.xml'):
            try:
                #Read the XML file and doing the JSON conversion
                xml = xmltodict.parse(archivo.read())
                objeto_json = convertXmltoJson(xml)
                return jsonify({'resultado': objeto_json})
            except Exception as e:
                return jsonify({'error': f'Error al procesar el archivo: {str(e)}'})
            
        return jsonify({'error': 'El archivo no tiene formato XML'})


@app.route('/cargar-texto', methods= ['GET','POST'])
def cargar_texto():
    if (request.method == "GET"):
        return render_template('loadingText.html')
    
    #verify that the file has been uploaded
    if 'plane_text' not in request.form:
        return jsonify({'error': 'No se ha proporcionado ningún archivo'})
    
    plane_text = request.form['plane_text']

    try:
        #Read the XML file and doing the JSON conversion
        object_json = convertTextToJson(plane_text)
        #object_json = object_json['{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine']
        
        #process cac:LegalMonetaryTotal section
        object_json = object_json['{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal']
        #reducing the key's name for more readable
        new_object_json = {}
        for key, value in object_json.items():
            modified_key = key.replace("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}", "")
            new_object_json[modified_key] = value
        return (new_object_json)
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'})


def convertTextToJson(plane_text):

    #parsear the xml
    root = ET.fromstring(plane_text)
    
    result = {}

    for child in root:
        if len(child) == 0:
            result[child.tag] = child.text
        else:
            result[child.tag] = convertTextToJson(ET.tostring(child))
    
    return result


def convertXmltoJson(xml):
    #open and read XML file
    purchasedItems = xml['Invoice'] 

    #empty list to store the data of XML
    values = []

    #process cac:invoiceline section
    for element in purchasedItems['cac:InvoiceLine']:
        data = {
            'id': element['cbc:ID'],
            'invoicedQuantity': element['cbc:InvoicedQuantity']['#text'],
            'lineExtensionAmount': element['cbc:LineExtensionAmount']['#text'],
            'cbc:PriceAmount': element['cac:Price']['cbc:PriceAmount']['#text'],
            'cbc:BaseQuantity': element['cac:Price']['cbc:BaseQuantity']['#text']
        }

        if 'cac:TaxTotal' in element:
            cac_TaxTotal = element['cac:TaxTotal']
            data['cac:TaxTotal'] = {
                'cbc:TaxAmount': cac_TaxTotal['cbc:TaxAmount']['#text'],
                'cbc:RoundingAmount': cac_TaxTotal['cbc:RoundingAmount']['#text']
            }
            cac_TaxSubtotal = element['cac:TaxTotal']['cac:TaxSubtotal']
            data['cac:TaxTotal']['cac:TaxSubtotal'] = {
            'cbc:TaxableAmount': cac_TaxSubtotal['cbc:TaxableAmount']['#text'],
            'taxSubtotalAmount': cac_TaxSubtotal['cbc:TaxAmount']['#text'],
            'cbc:Percent': cac_TaxSubtotal['cac:TaxCategory']['cbc:Percent']
            }

        if 'cac:Item' in element:
            #cac_Item = element['cac:Item']
            data['cac:Item'] = {
                'cbc:Description': element['cac:Item']['cbc:Description'],
                'cac:SellersItemIdentification': element['cac:Item']['cac:SellersItemIdentification']['cbc:ID']
            }
        values.append(data)
    #process cac:LegalMonetaryTotal section
    data2 = {
        'cbc:LineExtensionAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:LineExtensionAmount']['#text'],
        'cbc:TaxExclusiveAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:TaxExclusiveAmount']['#text'],
        'cbc:TaxInclusiveAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:TaxInclusiveAmount']['#text'],
        'cbc:AllowanceTotalAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:AllowanceTotalAmount']['#text'],
        'cbc:ChargeTotalAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:ChargeTotalAmount']['#text'],
        'cbc:PrepaidAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:PrepaidAmount']['#text'],
        'cbc:PayableRoundingAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:PayableRoundingAmount']['#text'],
        'cbc:PayableAmount': purchasedItems['cac:LegalMonetaryTotal']['cbc:PayableAmount']['#text']
    }
    values.append(data2)
    return values


if __name__ == '__main__':
    app.run(port= 5000, debug= True)