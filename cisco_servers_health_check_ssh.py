import paramiko
import time
import re
import threading
import os

def ssh_execute_commands_with_delay(ip_address, username, password, commands,
                                    output_file_base, prompt='admin:',
                                    command_timeout=300, total_timeout=120):
    """
    Establece una conexión SSH, espera el prompt y ejecuta una lista de comandos.
    Incluye la IP en el nombre del archivo.
    """

    # Crear el nombre de archivo único con la IP
    output_file = f"{output_file_base}_{ip_address.replace('.', '_')}.txt"

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Asegurarse de que el directorio de salida existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            try:
                ssh_client.connect(ip_address, username=username, password=password)
                shell = ssh_client.invoke_shell()
                output = ''

                # Espera inicial robusta para el prompt
                initial_wait_time = 15
                initial_wait_interval = 1
                initial_wait_attempts = int(initial_wait_time / initial_wait_interval)

                for attempt in range(initial_wait_attempts):
                    time.sleep(initial_wait_interval)
                    data = shell.recv(4096).decode('utf-8', errors='ignore')
                    output += data
                    print(f"Salida inicial recibida ({ip_address}): {output}")
                    if re.search(r'\n' + re.escape(prompt) + r'\s*$', output, re.MULTILINE):
                        break

                if not re.search(r'\n' + re.escape(prompt) + r'\s*$', output, re.MULTILINE):
                    print(f"Error ({ip_address}): No se detectó el prompt inicial después de {initial_wait_time} segundos.")
                    f.write(f"Error ({ip_address}): No se detectó el prompt inicial después de {initial_wait_time} segundos.\n")
                    ssh_client.close()
                    return

                # Limpiar la salida inicial
                output = output[output.rfind(prompt):]
                print(f"Salida inicial limpia ({ip_address}): {output}")

                # Ejecutar los comandos
                for command in commands:
                    print(f"Ejecutando comando ({ip_address}): {command}")
                    f.write(f"Ejecutando comando ({ip_address}): {command}\n")

                    shell.send(command + '\n')
                    time.sleep(5)

                    output = ''
                    start_time = time.time()
                    command_finished = False
                    paged_command = False

                    while time.time() - start_time < total_timeout:
                        try:
                            data = shell.recv(4096).decode('utf-8', errors='ignore')
                            if not data:
                                break
                            output += data
                            print(f"Salida recibida ({ip_address}): {output}")
                            time.sleep(1)

                            if re.search(r'Press <enter> for 1 line, <space> for one page, or <q> to quit', output):
                                paged_command = True
                                shell.send(' \n')
                                time.sleep(1)
                                output = output.replace(
                                    'Press <enter> for 1 line, <space> for one page, or <q> to quit',
                                    '')
                                continue

                            if re.search(r'\n' + re.escape(prompt) + r'\s*$', output, re.MULTILINE):
                                command_finished = True
                                break

                        except Exception as e:
                            print(f"Error al recibir datos ({ip_address}): {e}")
                            f.write(f"Error al recibir datos ({ip_address}): {e}\n")
                            break

                    print(f"Salida del comando ({ip_address}):")
                    print(output)
                    f.write(f"Salida del comando ({ip_address}):\n")
                    f.write(output)

                ssh_client.close()

            except paramiko.AuthenticationException:
                print(f"Error ({ip_address}): Autenticación fallida. Verifica el nombre de usuario y la contraseña.")
                f.write(f"Error ({ip_address}): Autenticación fallida. Verifica el nombre de usuario y la contraseña.\n")
            except paramiko.SSHException as e:
                print(f"Error de SSH ({ip_address}): {e}")
                f.write(f"Error de SSH ({ip_address}): {e}\n")
            except Exception as e:
                print(f"Ocurrió un error inesperado ({ip_address}): {e}")
                f.write(f"Ocurrió un error inesperado ({ip_address}): {e}\n")

    except Exception as e:
        print(f"Ocurrió un error general ({ip_address}): {e}")
        f.write(f"Ocurrió un error general ({ip_address}): {e}\n")

def run_ssh_on_multiple_servers(server_list, username, password, commands, output_file_base):
    threads = []
    for server in server_list:
        thread = threading.Thread(target=ssh_execute_commands_with_delay, args=(server, username, password, commands, output_file_base))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

# Ejemplo de uso con los seis servidores:
server_ips = ["10.26.16.10", "10.26.16.11", "10.25.191.10"]
cucm_username = "admin"
cucm_password = "admin"
commands_to_execute = [
    "show hardware",
    "show web-security",
    "show process load",
    "show network cluster",
    "utils ntp status",
    "show version inactive",
    "show version active",
    "system upgrade status",
    "show network eth0",
    "show status",
    "utils service list",
    "show cert list own",
    "utils system upgrade status",
    "utils dbreplication runtimestate",
    "utils diagnose test"
]

output_file_base = "D:\Cloverhound\Clients\Wilmington\LogsServer07262025"

run_ssh_on_multiple_servers(server_ips, cucm_username, cucm_password, commands_to_execute, output_file_base)
