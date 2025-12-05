#!/usr/bin/env python3
# encoding: utf-8
"""
automove.py: monitorea un directorio para mover todos los archivos que encuentre
                concordando con cierto filtro (expresión). Mueve a un directorio dado
Created by Ramón Barrios Láscar, 2025-04-12
Modificado, Ramón Barrios Láscar, 2025-04-30: agregado un máximo de vueltas sin mover
Modificado, Ramón Barrios Láscar, 2025-05-11: agregado manejo de directorios
Modificado, Ramón Barrios Láscar, 2025-06-28: agregado la opción -x/--execute para ejecutar un comando
"""

import os
import time
import logging
from optparse import OptionParser
import shutil
import sys
import re
import subprocess # Import the subprocess module

# Configuración básica del logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )
def saned(src_str, to_sanitize=r'\(\)\[\]'):
    """
    Sanitizes a string, specifically for dragged paths in macOS,
    by removing backslashes preceding spaces and characters in to_sanitize.

    Args:
        src_str: The input string (likely a dragged file path).
        to_sanitize: A string containing characters to sanitize.
                      The backslash in the default value is treated literally.

    Returns:
        The sanitized string with backslashes removed before specified characters
        and spaces.
    """
    # Ensure to_sanitize is treated as literal characters in the regex
    pattern = r'\\([' + re.escape(to_sanitize) + r' ])'
    sanitized_str = re.sub(pattern, r'\1', src_str)
    return sanitized_str

def input_w_default(prompt, default_value):
    """
    Asks the user for input with a default value.

    Args:
        prompt: The message to display to the user. Include the default value
                within the prompt for clarity.
        default_value: The value to be used if the user presses Enter.

    Returns:
        The user's input as a string, or the default value if the user
        presses Enter.
    """
    user_input = input(f"{prompt} [{default_value}]: ")
    if user_input == "":
        return default_value
    else:
        return user_input

def mon_move(src_dir, tgt_dir, filt, wait, maxnoop, do_execute=None):
    """
    Monitorea el directorio de origen por archivos que coincidan con el filt
    y los mueve al directorio de destino.

    Args:
        src_dir (str): Ruta al directorio de origen.
        tgt_dir (str): Ruta al directorio de destino.
        filt (str): Cadena de texto para filtrar los nombres de archivo (regex).
        wait (int): Número de segundos para esperar entre revisión y revisión.
        maxnoop (int): Número máximo de segundos sin encontrar archivos antes de terminar.
        do_execute (str): Comando a ejecutar después de mover, con '{}' como placeholder.
    """
    logging.info(f"Monitoreando el directorio: {src_dir}")
    logging.info(f"Moviendo archivos y directorios coincidentes a: {tgt_dir}")
    logging.info(f"Filtrando nombres con la expresión regular: '{filt}'")
    logging.info(f"Esperando {wait} segundos entre revisión y revisión")
    logging.info(f"Terminando si no se encuentran elementos nuevos por {maxnoop} segundos.")
    if do_execute:
        logging.info(f"Se ejecutará el comando: '{do_execute}' después de mover cada elemento.")

    if not os.path.exists(tgt_dir):
        try:
            os.makedirs(tgt_dir)
            logging.info(f"Directorio de destino creado: {tgt_dir}")
        except OSError as e:
            logging.error(f"Error al crear el directorio de destino '{tgt_dir}': {e}")
            return

    pat = re.compile(filt)

    found_items = set()
    noop_count = 0

    while True:
        try:
            src_items = set(os.listdir(src_dir))
            new_items = src_items - found_items

            if not new_items:
                noop_count += 1
                logging.debug(f"No se encontraron elementos nuevos en este ciclo. Ciclos inactivos: {noop_count}/{maxnoop}")
                if noop_count * wait >= maxnoop:
                    logging.info(f"No se encontraron elementos nuevos durante {maxnoop} segundos. Terminando.")
                    break
            else:
                noop_count = 0  # Reset the no-operation counter

            for item_name in new_items:
                src_path = os.path.join(src_dir, item_name)
                tgt_path = os.path.join(tgt_dir, item_name)

                if pat.search(item_name):
                    try:
                        if os.path.isfile(src_path):
                            shutil.move(src_path, tgt_path)
                            logging.info(f"Movido archivo '{src_path}' -> '{tgt_path}'")
                        elif os.path.isdir(src_path):
                            logging.info(f"Esperando {wait} segundos adicionales antes de mover")
                            time.sleep(wait)  # Esperar antes de intentar mover
                            shutil.move(src_path, tgt_path)
                            logging.info(f"Movido directorio '{src_path}' -> '{tgt_path}'")
                        else:
                            logging.warning(f"Elemento '{src_path}' no es ni archivo ni directorio. Ignorando.")

                        # --- NEW: Execute command if specified ---
                        if do_execute:
                            command_to_run = do_execute.replace('{}', f'"{tgt_path}"') # Enclose path in quotes
                            logging.info(f"Ejecutando comando: {command_to_run}")
                            try:
                                # Use shell=True for simpler command parsing if needed, but be cautious with untrusted input
                                # For more control and security, split the command into a list and use shell=False
                                subprocess.run(command_to_run, shell=True, check=True, capture_output=True, text=True)
                                logging.info(f"Comando ejecutado exitosamente.")
                            except subprocess.CalledProcessError as e:
                                logging.error(f"Error al ejecutar el comando para '{tgt_path}': {e}")
                                logging.error(f"  Stdout: {e.stdout}")
                                logging.error(f"  Stderr: {e.stderr}")
                            except Exception as e:
                                logging.error(f"Error inesperado al ejecutar el comando para '{tgt_path}': {e}")

                    except Exception as e:
                        logging.error(f"Error al mover '{item_name}': {e}")

            found_items = src_items
            time.sleep(wait)  # Intervalo de chequeo
        except FileNotFoundError:
            logging.error(f"El directorio de origen '{src_dir}' no fue encontrado.")
            return
        except Exception as e:
            logging.error(f"Ocurrió un error durante el monitoreo: {e}")
            time.sleep(10)  # Esperar un poco más en caso de error

if __name__ == "__main__":
    try:
        parser = OptionParser(usage="usage: %prog -o <src_dir> -d <tgt_dir> -f <filt> [-w <wait>] [-m <maxnoop>] [-I] [-x <command>]")
        parser.add_option("-o", "--origen", dest="src_dir", help="Directorio de origen a monitorear", default=".")
        parser.add_option("-d", "--destino", dest="tgt_dir", help="Directorio de destino para mover los archivos", default="/tmp")
        parser.add_option("-f", "--filtro", dest="filt", help="Filtro (expresión regular) para los nombres de archivo", default="Screenshot *")
        parser.add_option("-w", "--espera", dest="wait", help="Tiempo de espera (en segundos)", default=5, type="int")
        parser.add_option("-m", "--maxnoop", dest="maxnoop", help="Número máximo de segundos sin archivos antes de terminar", default=3600, type="int")
        parser.add_option("-I", "--interactivo", dest="interactive", help="Modo interactivo", action="store_true", default=False)
        parser.add_option("-x", "--execute", dest="do_execute", help="Ejecutar un comando después de mover. Use '{}' como marcador de posición para la ruta del archivo movido.", action="store", default="afplay /Users/e/Library/Sounds/mac-sound-pack-pop.m4r")

        (options, args) = parser.parse_args()

        src_dir = os.path.expanduser(os.path.expandvars(options.src_dir))
        tgt_dir = os.path.expanduser(os.path.expandvars(options.tgt_dir))
        filt = options.filt
        wait = options.wait
        maxnoop = options.maxnoop
        do_execute = options.do_execute # Get the execute command

        if options.interactive:
            src_dir = saned(input_w_default("Directorio origen", src_dir).replace('\\ ', ' ').strip())
            tgt_dir = saned(input_w_default("Directorio destino", tgt_dir).replace('\\ ', ' ').strip())
            filt = input_w_default("Filtro de nombres de archivo", filt)
            try:
                wait = int(input_w_default("Espera entre segundos", wait))
            except ValueError as e:
                logging.warning(f"{e}")
                wait = 5
                logging.warning(f"Usando el predeterminado de {wait} segundos")
            try:
                maxnoop = int(input_w_default("Máximo de segundos sin operaciones", maxnoop))
            except ValueError as e:
                logging.warning(f"{e}")
                maxnoop = 3600
                logging.warning(f"Usando el predeterminado de {maxnoop} segundos")
            do_execute = input_w_default("Comando a ejecutar después de mover (dejar vacío si no aplica)", do_execute if do_execute is not None else "")
            if do_execute == "":
                do_execute = None # Ensure it's None if empty string is entered


        if not os.path.isdir(src_dir):
            logging.error(f"El directorio de origen '{src_dir}' no es un directorio válido.")
        elif not os.path.exists(tgt_dir):
            logging.warning(f"El directorio de destino '{tgt_dir}' no existe. Se intentará crear.")
            mon_move(src_dir, tgt_dir, filt, wait, maxnoop, do_execute) # Pass do_execute
        elif not os.path.isdir(tgt_dir):
            logging.error(f"El directorio de destino '{tgt_dir}' no es un directorio válido.")
        else:
            mon_move(src_dir, tgt_dir, filt, wait, maxnoop, do_execute) # Pass do_execute
    except KeyboardInterrupt:
        logging.error(f"automove: proceso cancelado")