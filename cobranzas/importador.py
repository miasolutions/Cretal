from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from cobranzas import ALLOWED_EXTENSIONS
from cobranzas.auth import login_required
from cobranzas.db import get_db
from datetime import datetime, date
import json
import uuid
import requests
import os

bp = Blueprint('importador', __name__)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/importador', methods=('GET', 'POST'))
@login_required
def importador():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó un archivo.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            #file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            #flash('Archivo enviado con éxito. Procesando...')
            clasificarTxtCobranza(file)
        else:
            flash('El archivo seleccionado no es de extensión txt.')

    return render_template('importador.html')

def clasificarTxtCobranza(file):
    f = (file.stream.read()).decode('utf-8')

    with open('cobranzas\\cobranzas.json') as cobranza:
        cobranzaJson = json.load(cobranza)
        cobranza.close()

    # token = requests.get('https://api.teamplace.finneg.com/api/oauth/token?grant_type=client_credentials&client_id=fc780dabfafc6095be68dd611a754cf8&client_secret=71f6a2a7a5cd77cedcc031db44bc673f').text
    token = requests.get(
        'https://api.teamplace.finneg.com/api/oauth/token?grant_type=client_credentials&client_id=59427de0d16ab3d4da22f078dc384542&client_secret=7d2f720431acf4094821b11a096a7fb2').text
    # RED LINK
    if request.form.get('bancos') == 'redLink':
        if f[0:3] == '0AZE':
            i = 1
            ok = 0
            notOk = 0
            while True:
                if f[100 * i] == '1':
                    importeMonPrincipal = int(f[(28+100*i):(40+100*i)]) / 100
                    nroComprobante = int(f[(48+100*i):(98+100*i)])
                    codigoCliente = int(f[(9+100*i):(28+100*i)])
                    fechaComprobante = f'{f[(40+100*i):(44+100*i)]}-{f[(44+100*i):(46+100*i)]}-{f[(46+100*i):(48+100*i)]}'
                    
                    r = armarCobranza(importeMonPrincipal, nroComprobante, codigoCliente, fechaComprobante, token, cobranzaJson)

                    if r.status_code == 200:
                        ok += 1
                    else:
                        notOk += 1

                    i += 1
                else:
                    break
            flash(f'Se encontró un total de {i-1} cobranzas. Insertadas: {ok}. Fallidas: {notOk}')
        else:
            flash('El archivo enviado no coincide con el banco seleccionado.')

    # BANCO PROVINCIA
    elif request.form.get('bancos') == 'bancoProvincia':
        if f[0:5] == "DATOS":
            i = 0   # Cursor
            cantCobranzas = 0
            ok = 0
            notOk = 0
            while True:
                try:
                    if f[i] == 'D':
                        nroTransaccion = int(f[(58+i):(66+i)])
                        importeMonPrincipal = int(f[(177+i):(183+i)]) / 100
                        #nroComprobante = int(f[(28+i):(48+i)])  #Obtener de la API MTEC_DatosFacturaCobranza
                        #codigoCliente = int(f[(54+i):(66+i)])   #Obtener de la API MTEC_DatosFacturaCobranza
                        fechaComprobante = f'20{f[(224+i):(226+i)]}-{f[(226+i):(228+i)]}-{f[(228+i):(230+i)]}'
                        
                        # Llamo al MTECDatosFacturaCobranza para que me de los códigos de comprobante y de cliente.
                        r = requests.get(f'https://api.teamplace.finneg.com/api/reports/MTECDatosFacturaCobranza?ACCESS_TOKEN={token}&transaccionid={nroTransaccion}')

                        if r.json() is None:
                            nroComprobante = r.json()[0]['IDENTIFICACIONEXTERNA']
                            codigoCliente = r.json()[0]['CLIENTECODIGO']
                        else:
                            nroComprobante = 0      # No hay factura de venta en finnegans para el número de transacción que se pasó
                            codigoCliente = 0       # Por ende tampoco hay cliente.

                        r = armarCobranza(importeMonPrincipal, nroComprobante, codigoCliente, fechaComprobante, token, cobranzaJson)

                        if r.status_code == 200:
                            ok += 1
                        else:
                            notOk += 1

                        i += 281
                        cantCobranzas += 1
                    else:
                        break
                except IndexError:
                    break
            
            flash(f'Se encontró un total de {cantCobranzas} cobranzas. Insertadas: {ok}. Fallidas: {notOk}')
        else:
            flash('El archivo enviado no coincide con el banco seleccionado.')
    
    # BANCO NACION
    elif request.form.get('bancos') == 'bancoNacion':
        print("ENTRO A BANCO NACION")

        i = 0  # Cursor
        cantCobranzas = 0
        ok = 0
        notOk = 0
        while True:
            try:
                codigoEmpresa = int(f[(0 + i):(10 + i)])
                print("CODIGO EMPRESA: ", codigoEmpresa)
                numeroSucursal = int(f[(10 + i):(14 + i)])
                print("NUMERO SUCURSAL: ", numeroSucursal)
                numeroTerminal = int(f[(14 + i):(18 + i)])
                print("NUMERO TERMINAL: ", numeroTerminal)
                anio1 = int(f[(18 + i):(22 + i)])
                print("AÑO: ", anio1)
                mes1 = int(f[(22 + i):(24 + i)])
                print("MES: ", mes1)
                dia1 = int(f[(24 + i):(26 + i)])
                print("DIA: ", dia1)
                anio2 = int(f[(26 + i):(30 + i)])
                print("AÑO: ", anio2)
                mes2 = int(f[(30 + i):(32 + i)])
                print("MES: ", mes2)
                dia2 = int(f[(32 + i):(34 + i)])
                print("DIA: ", dia2)
                nroTransaccion = int(f[(34 + i):(42 + i)])
                print("NRO TRANSACCION: ", nroTransaccion)

                importeMonPrincipal = int(f[(42 + i):(57 + i)])
                print("IMPORTE MON PRINCIPAL: ", importeMonPrincipal)

                #calculamos la fecha a partir de las variables anio1 mes1 dia1
                fechaComprobante = f'{anio1}-{mes1}-{dia1}'
                print("FECHA COMPROBANTE: ", fechaComprobante)
                # Llamo al MTECDatosFacturaCobranza para que me de los códigos de comprobante y de cliente.
                urlRequest = f'https://api.teamplace.finneg.com/api/reports/MTECDatosFacturaCobranza?ACCESS_TOKEN={token}&transaccionid={nroTransaccion}'
                print("URL REQUEST: ", urlRequest)
                r = requests.get(urlRequest)
                print ("CONSULTANDO LA URL: ")
                print("R.JSON: ", r.json)
                if r.json:
                    nroComprobante = 0  # No hay factura de venta en finnegans para el número de transacción que se pasó
                    codigoCliente = 0  # Por ende tampoco hay cliente.
                else:
                    nroComprobante = r.json()[0]['IDENTIFICACIONEXTERNA']
                    codigoCliente = r.json()[0]['CLIENTECODIGO']


                # nroComprobante = 0  # No hay factura de venta en finnegans para el número de transacción que se pasó
                # codigoCliente = 0  # Por ende tampoco hay cliente.
                print("NRO COMPROBANTE: ", nroComprobante)
                print("CODIGO CLIENTE: ", codigoCliente)
                r = armarCobranza(importeMonPrincipal, nroComprobante, codigoCliente, fechaComprobante, token,
                                        cobranzaJson)

                if r.status_code == 200:
                    ok += 1
                else:
                    notOk += 1

                i += 162
                cantCobranzas += 1
                print("CANTIDAD DE COBRANZAS: ", cantCobranzas)
            except IndexError:
                break

        flash(f'Se encontró un total de {cantCobranzas} cobranzas. Insertadas: {ok}. Fallidas: {notOk}')

    
    # BANCO HSBC
    elif request.form.get('bancos') == 'bancoHSBC':
        pass

    else:
        flash('El archivo enviado no corresponde a cobranzas.')

def armarCobranza(importeMonPrincipal, nroComprobante, codigoCliente, fechaComprobante, token, cobranzaJson):
    cobranzaJson['CtaCte'][0]['ImporteMonPrincipal'] = importeMonPrincipal
    cobranzaJson['CtaCte'][0]['AplicacionOrigen'] = str(nroComprobante)
    cobranzaJson['CtaCte'][0]['ImporteMonTransaccion'] = importeMonPrincipal
    cobranzaJson['Banco'][0]['ImporteMonTransaccion'] = importeMonPrincipal
    cobranzaJson['Proveedor'] = str(codigoCliente)
    cobranzaJson['IdentificacionExterna'] = str(uuid.uuid4())
    cobranzaJson['Fecha'] = date.today().isoformat()
    cobranzaJson['FechaCobranza'] = fechaComprobante

    r = requests.post(f'https://api.teamplace.finneg.com/api/cobranza?ACCESS_TOKEN={token}', json=cobranzaJson)
    print(r.json())

    return r

        # codEnte = f[1:4]
        # fecha = datetime.strptime(f[4:12], '%Y%m%d').strftime('%Y-%m-%d')

        #cobranzaJson['CtaCte']['ImporteMonPrincipal'] = 
        #print(fecha)