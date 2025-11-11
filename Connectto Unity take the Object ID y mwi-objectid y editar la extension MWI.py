import requests
import xml.etree.ElementTree as ET
import os

# Deshabilita las advertencias de SSL para entornos de prueba (NO RECOMENDADO EN PRODUCCIÓN SIN VERIFICACIÓN SSL VÁLIDA)
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# --- Configuración de Unity Connection ---
CUC_IP = "69.168.17.32" # Reemplaza con la IP/Hostname de tu CUC
CUC_USERNAME = "partneradmin" # Reemplaza con tu usuario administrador de CUC
CUC_PASSWORD = "pG9{y0#GC!C3_K" # Reemplaza con tu contraseña de administrador de CUC

# --- Lista de alias y sus nuevas extensiones MWI ---
# ¡IMPORTANTE! Reemplaza estos valores con tus alias reales y las nuevas extensiones MWI deseadas.
alias_new_mwi_extensions = {
    "dapollard@ua.edu": "252584251",
    "aabernat@ua.edu": "252585997",
    # Ejemplo adicional si quieres cambiar la que ya usas
    # Agrega más alias y sus nuevas extensiones aquí
    # "otro_alias@dominio.com": "nueva_extension",
}

user_mwi_details = {} # Diccionario para almacenar alias: {user_object_id, mwi_object_id, current_mwi_extension}
output_lines = [] # Lista para almacenar las líneas que se escribirán en el archivo

# --- Configuración de la ruta y nombre del archivo de salida ---
output_directory = r"D:\Python Projects\Salidas\CambioMWIObjetID"
output_filename = "MWI_Update_Log.txt" # Cambiado a un nombre más descriptivo
output_filepath = os.path.join(output_directory, output_filename)

# --- Crear el directorio si no existe ---
if not os.path.exists(output_directory):
    print(f"Creando el directorio: {output_directory}")
    os.makedirs(output_directory)

print("Iniciando el proceso de obtención y actualización de MWI para los siguientes alias:")
for alias, new_ext in alias_new_mwi_extensions.items():
    print(f"- {alias} (Nueva Ext: {new_ext})")
output_lines.append("--- Lista de Alias a Procesar ---")
output_lines.extend([f"- {alias} (Nueva Ext: {new_ext})" for alias, new_ext in alias_new_mwi_extensions.items()])
output_lines.append("\n--- Resultados del Proceso ---")

# --- Bucle para consultar cada alias y luego sus MWIs, y finalmente actualizar ---
for alias, new_mwi_extension in alias_new_mwi_extensions.items():
    user_object_id = None
    mwi_object_id = None
    current_mwi_extension = None

    # Paso 1: Obtener el User ObjectId
    user_url = f"https://{CUC_IP}/vmrest/users?query=(alias%20is%20{alias})"
    headers = {"Accept": "application/xml"}

    try:
        user_response = requests.get(
            user_url,
            auth=(CUC_USERNAME, CUC_PASSWORD),
            headers=headers,
            verify=False
        )
        user_response.raise_for_status()

        user_root = ET.fromstring(user_response.content)
        user_id_element = user_root.find(".//User/ObjectId")

        if user_id_element is not None:
            user_object_id = user_id_element.text
            print(f"\n[{alias}] User ObjectId obtenido: {user_object_id}")
            output_lines.append(f"\n[{alias}] User ObjectId obtenido: {user_object_id}")

            # Paso 2: Obtener los MWIs para este User ObjectId
            mwi_list_url = f"https://{CUC_IP}/vmrest/users/{user_object_id}/mwis"
            
            mwi_list_response = requests.get(
                mwi_list_url,
                auth=(CUC_USERNAME, CUC_PASSWORD),
                headers=headers,
                verify=False
            )
            mwi_list_response.raise_for_status()

            mwi_root = ET.fromstring(mwi_list_response.content)
            
            mwi_elements = mwi_root.findall(".//Mwi")
            
            if mwi_elements:
                # Lógica para seleccionar el MWI correcto.
                # Aquí, por simplicidad, tomamos el primer MWI.
                # SI UN USUARIO TIENE VARIOS MWIs y necesitas el específico,
                # tendrías que añadir lógica aquí para filtrarlos por DisplayName, MwiExtension, etc.
                # Ejemplo: for mwi in mwi_elements:
                #             if mwi.find("DisplayName").text == "MWI-Principal":
                #                 first_mwi = mwi
                #                 break
                first_mwi = mwi_elements[0] # Tomamos el primer MWI encontrado
                mwi_object_id = first_mwi.find("ObjectId").text
                current_mwi_extension_element = first_mwi.find("MwiExtension")
                if current_mwi_extension_element is not None:
                    current_mwi_extension = current_mwi_extension_element.text

                print(f"[{alias}] MWI ObjectId obtenido: {mwi_object_id} (Extensión Actual: {current_mwi_extension})")
                output_lines.append(f"[{alias}] MWI ObjectId obtenido: {mwi_object_id} (Extensión Actual: {current_mwi_extension})")
                
                user_mwi_details[alias] = {
                    "user_object_id": user_object_id,
                    "mwi_object_id": mwi_object_id,
                    "current_mwi_extension": current_mwi_extension
                }

                # Paso 3: Realizar la solicitud PUT para actualizar la MwiExtension
                put_url = f"https://{CUC_IP}/vmrest/users/{user_object_id}/mwis/{mwi_object_id}"
                
                # Construir el cuerpo XML para la actualización
                # Aquí puedes incluir solo los campos que quieres cambiar.
                # Los campos en tu ejemplo: Active, DisplayName, MwiExtension, MwiOn, UsePrimaryExtension
                # Asegúrate de mantener los valores correctos para MwiOn, Active, UsePrimaryExtension
                update_xml_body = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Mwi>
  <Active>true</Active>
  <DisplayName>MWI</DisplayName>
  <MwiExtension>{new_mwi_extension}</MwiExtension>
  <MwiOn>false</MwiOn>
  <UsePrimaryExtension>false</UsePrimaryExtension>
</Mwi>""" # Ajusta UsePrimaryExtension según tu necesidad

                headers_put = {
                    "Content-Type": "application/xml",
                    "Accept": "application/xml"
                }

                print(f"[{alias}] Intentando actualizar MWI a: {new_mwi_extension}...")
                output_lines.append(f"[{alias}] Intentando actualizar MWI a: {new_mwi_extension}...")
                
                put_response = requests.put(
                    put_url,
                    auth=(CUC_USERNAME, CUC_PASSWORD),
                    headers=headers_put,
                    data=update_xml_body,
                    verify=False
                )
                put_response.raise_for_status() # Lanza error si no es 2xx

                # Si la solicitud PUT fue exitosa (código 200 OK, 204 No Content, etc.)
                print(f"[{alias}] MWI actualizado exitosamente a: {new_mwi_extension}")
                output_lines.append(f"[{alias}] MWI actualizado exitosamente a: {new_mwi_extension}")

            else:
                warning_msg = f"[{alias}] Advertencia: No se encontraron MWIs para el usuario. No se pudo actualizar."
                print(warning_msg)
                output_lines.append(warning_msg)

        else:
            warning_msg = f"[{alias}] Advertencia: No se encontró User ObjectId para el alias. No se pudo procesar."
            print(warning_msg)
            output_lines.append(warning_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Error al procesar o actualizar MWI para alias {alias}: {e}"
        print(error_msg)
        output_lines.append(error_msg)
        # Intentar obtener el contenido de la respuesta de error si está disponible
        if 'user_response' in locals() and user_response:
            output_lines.append(f"  Respuesta User API: {user_response.content.decode('utf-8')}")
        if 'mwi_list_response' in locals() and mwi_list_response:
            output_lines.append(f"  Respuesta MWI List API: {mwi_list_response.content.decode('utf-8')}")
        if 'put_response' in locals() and put_response:
            output_lines.append(f"  Respuesta PUT API: {put_response.content.decode('utf-8')}")

# --- Escribir los resultados en el archivo ---
output_lines.append("\n--- Resumen Final del Proceso ---")
if user_mwi_details:
    for alias, details in user_mwi_details.items():
        output_lines.append(f"Alias: {alias}")
        output_lines.append(f"  User ObjectId: {details.get('user_object_id', 'N/A')}")
        output_lines.append(f"  MWI ObjectId: {details.get('mwi_object_id', 'N/A')}")
        output_lines.append(f"  Ext. Original MWI: {details.get('current_mwi_extension', 'N/A')}")
        output_lines.append(f"  Ext. Nueva MWI: {alias_new_mwi_extensions.get(alias, 'N/A')}")
        output_lines.append("") # Línea en blanco para separar
else:
    output_lines.append("No se procesaron Object IDs para los alias especificados.")

try:
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"\nResultados del log guardados exitosamente en: {output_filepath}")
except IOError as e:
    print(f"\nError al guardar el archivo en {output_filepath}: {e}")