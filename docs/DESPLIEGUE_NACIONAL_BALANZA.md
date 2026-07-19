# Despliegue nacional con balanza USB-serial

## Objetivo operativo

Cada PC debe poder iniciar la aplicacion y la balanza con un solo comando. Si la balanza no esta conectada, el puente queda vigilando y se conecta cuando aparezca un puerto serial.

## Windows

Ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```

El script:

- crea o usa un entorno virtual Python;
- instala dependencias;
- crea `.env` si falta;
- ejecuta migraciones;
- valida Django;
- levanta el servidor;
- levanta el puente automatico de balanza;
- abre la aplicacion en el navegador.

## Linux

Ejecutar:

```bash
bash scripts/start_all.sh
```

En Linux, si el usuario no tiene permiso para leer el puerto serial, agregarlo al grupo correspondiente y reiniciar sesion:

```bash
sudo usermod -aG dialout "$USER"
```

En algunas distribuciones el grupo puede ser `uucp` o `tty`.

## Diagnostico

Endpoint local:

```text
http://127.0.0.1:8000/balanza/diagnostico/
```

Puente multiplataforma:

```bash
python scripts/weight_bridge.py --list-ports
python scripts/weight_bridge.py --once
```

## Que corrige automaticamente

- detecta COM/ttyUSB/ttyACM disponibles;
- reintenta si el USB se desconecta;
- evita pelear por el COM usando el puente como fuente preferida;
- prueba baudios y modos seriales configurados;
- valida estabilidad antes de enviar el peso;
- reinicia servidor o puente si se caen durante `auto_start.py`;
- ignora lecturas antiguas para no registrar pesos vencidos.

## Que no puede corregir solo

- driver de adaptador USB-serial no instalado;
- cable RS232 incorrecto o cruzado cuando la balanza requiere otro pinout;
- balanza sin energia DC 5V 1A;
- adaptador USB con chip incompatible o clonado;
- protocolo propietario no documentado;
- permisos Linux sin reinicio de sesion despues de agregar grupo.

Para equipos nacionales, estandarizar el adaptador USB-RS232. Preferir FTDI o un modelo con driver oficial Windows 10/11 y soporte Linux.

## Variables utiles

```text
WEIGHT_BRIDGE_FIRST=True
WEIGHT_DIRECT_READ_ENABLED=True
WEIGHT_READING_MAX_AGE_SECONDS=10
BALANZA_SERIAL_PORTS=
BALANZA_SERIAL_BAUDRATES=9600,4800,2400,1200,19200,38400,57600,115200
BALANZA_SERIAL_MODES=8N1,7E1,8E1,7N1,8N2
BALANZA_LINE_CONTROLS=default,rts,dtr_rts,none
BALANZA_READ_SECONDS=4
BALANZA_STABLE_SAMPLES=3
BALANZA_STABLE_TOLERANCE_KG=0.020
BALANZA_DIRECT_MAX_ATTEMPTS=32
BALANZA_POLL_COMMANDS=S\r\n,W\r\n,P\r\n,SI\r\n,Q\r\n,PRINT\r\n
```

Si una sede fija el puerto manualmente:

```text
BALANZA_SERIAL_PORTS=COM6
```

o en Linux:

```text
BALANZA_SERIAL_PORTS=/dev/ttyUSB0
```
