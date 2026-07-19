# Integracion balanza HBA-800 por USB-serial

## Modo recomendado en Windows

La HBA-800 de las fotos debe tratarse como balanza RS232 conectada mediante adaptador USB-serial. En Windows el modo mas estable es:

1. Iniciar Django:

```powershell
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

2. En otra consola, iniciar el puente:

```powershell
.\venv\Scripts\python.exe .\scripts\weight_bridge.py
```

Alternativa Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\weight_bridge.ps1
```

3. Registrar el residuo desde la app y presionar `Conectar balanza`.

El endpoint `balanza/leer/` prefiere una lectura reciente del puente. Esto evita que Django y el puente intenten abrir el mismo `COM` al mismo tiempo.

## Diagnostico rapido

Listar puertos COM:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\weight_bridge.ps1 -ListPorts
```

Probar una deteccion unica:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\weight_bridge.ps1 -Once
```

Si se sabe el puerto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\weight_bridge.ps1 -Ports COM6 -Once
```

Desde la app, el endpoint de diagnostico es:

```text
/balanza/diagnostico/
```

## Configuracion en `.env`

Valores recomendados:

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

Si Windows cambia el puerto, se puede fijar:

```text
BALANZA_SERIAL_PORTS=COM6
```

## Problemas comunes

- `Acceso denegado`: otro programa ya tiene abierto el COM. Cerrar puente duplicado, PuTTY, Arduino IDE, RealTerm u otro lector serial.
- No aparece ningun COM: falta driver del adaptador USB-serial o el cable no esta conectado.
- Aparece COM pero no hay datos: revisar energia DC 5V 1A, cable RS232 correcto, boton `PRINT` de la balanza o protocolo de transmision.
- En Windows falla y en Linux funciona: normalmente es driver del adaptador o chip USB-serial viejo/clonado.

Para una demo estable, usar un adaptador USB-RS232 con chip FTDI o uno con driver oficial compatible con Windows 10/11.
