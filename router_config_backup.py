import subprocess
import os

def ejecutar_comando_plink_guardar(ip_address, username, password, comando, output_folder):
    """
    Ejecuta un comando en un dispositivo remoto usando plink y guarda la salida en un archivo.
    """
    try:
        plink_path = r"C:\Program Files\PuTTY\plink.exe"  # Asegúrate de que esta sea la ruta correcta.
        output_file = os.path.join(output_folder, f"{ip_address.replace('.', '_')}_show_run.txt")

        plink_command = [
            plink_path,
            "-ssh",
            "-pw",
            password,
            f"{username}@{ip_address}",
            comando,
        ]

        resultado = subprocess.run(plink_command, capture_output=True, text=True, check=False)

        with open(output_file, "w") as f:
            f.write(resultado.stdout)
            if resultado.stderr:
                f.write("\n\nERRORES:\n")
                f.write(resultado.stderr)

        print(f"Comando '{comando}' ejecutado en {ip_address}. La salida se guardó en: {output_file}")

    except FileNotFoundError:
        print(f"Error: plink.exe no se encontró en la ruta especificada.")
    except Exception as e:
        print(f"Ocurrió un error al ejecutar el comando en {ip_address}: {e}")

# Lista de IPs de los routers Cisco
router_ips = [
    "10.10.16.1",
"10.10.83.10",
"10.10.63.5",
"10.10.71.10",
"10.10.20.1",
"10.10.98.5",
"10.10.62.10",
"10.10.31.10",
"10.10.94.10",
"10.10.95.10",
]

# Credenciales SSH
ssh_username = "admin"
ssh_password = "admin"

# Comando a ejecutar
comando_a_ejecutar = "show run"

# Carpeta para guardar la salida
output_ruta = r"C:\Users\nhaf3\OneDrive\Escritorio\UofA Routers VG"

# Crear la carpeta si no existe
os.makedirs(output_ruta, exist_ok=True)

# Iterar sobre la lista de IPs y ejecutar el comando guardando la salida
for ip in router_ips:
    ejecutar_comando_plink_guardar(ip, ssh_username, ssh_password, comando_a_ejecutar, output_ruta)

print("Proceso completado.")
