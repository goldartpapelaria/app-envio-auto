from flask import Flask, request
import smtplib
from email.message import EmailMessage
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

app = Flask(__name__)

# Autenticar com Google Drive
gauth = GoogleAuth()
gauth.CommandLineAuth()  # abrirá o navegador para login na primeira vez
drive = GoogleDrive(gauth)

# Mapeamento de produto para ID de arquivo no Drive
PRODUCT_ZIP_MAP = {
    "ARQUIVO DIGITAL ALICE 60": "1y0Afsdyde1fR-2IA6OT27wh-9MkTCANV",
    # Adicione outros produtos aqui
}

# Função para baixar o arquivo do Google Drive
def download_zip_file(file_id, filename):
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(filename)

# Função para enviar e-mail com anexo ZIP
def send_zip_email(recipient, zip_filename):
    msg = EmailMessage()
    msg['Subject'] = 'Seu arquivo digital está pronto para download!'
    msg['From'] = 'goldartpapelaria@gmail.com'
    msg['To'] = recipient
    msg.set_content('Obrigado pela sua compra! Segue o arquivo em anexo.')

    with open(zip_filename, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='zip', filename=zip_filename)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('goldartpapelaria@gmail.com', 'SUA_SENHA_DE_APP_AQUI')  # Substituir depois
        smtp.send_message(msg)

# Rota para receber webhook da Nuvemshop
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    status = data.get("status")
    if status != "paid":
        return {"message": "Pagamento não confirmado"}, 200

    buyer_email = data.get("buyer", {}).get("email")
    product_title = data.get("products", [{}])[0].get("name")

    if not buyer_email or not product_title:
        return {"message": "Dados incompletos"}, 400

    file_id = PRODUCT_ZIP_MAP.get(product_title)
    if not file_id:
        return {"message": "Produto não encontrado"}, 404

    zip_filename = f"{product_title}.zip"
    download_zip_file(file_id, zip_filename)
    send_zip_email(buyer_email, zip_filename)
    os.remove(zip_filename)  # limpar o arquivo local depois de enviar

    return {"message": "Arquivo enviado com sucesso"}, 200

if __name__ == '__main__':
    app.run(debug=True)
