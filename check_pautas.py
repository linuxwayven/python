#!/usr/bin/python
############################################################################
# title           : check_pautas.py
# description     : This script check pautas for a word given.
# author          : Jesus A. Ruiz
# date            : 14-06-2016
# version         : 1.0
# usage           : check_pautas.py
# notes           :
# python_version  : 2.6.4
############################################################################

# Import Modules Section
import os
import shutil
import sys
import socket
import glob
import datetime
import re
import time
import math

# Global Variables Section
base_dir =                      "/tmp/felipe/check_pautas"
output_line =                   ""
run_hostname =                  socket.gethostname()
output_file =                   base_dir + "/output_file.txt"
src_directory_pautas =          "/u00/appl/base/bin"
dst_directory_pautas =          base_dir + "/pautas_processed"
pautas_list_filename =          "listado_pautas_a_chequear_icalma.txt"
pautas_output_filename =        "lista_pautas_con_ftp.txt"
log_output_filename =           "lista_pautas_con_ftp.log"
pautas_exception_filename =     "lista_pautas_con_errores.txt"
pautas_to_check_filename =      "lista_pautas_a_chequear.txt"
src_directory_logs =            "/u03/explota/base_exp/logs"
providers_tuple =               ('ALQUIMIA', 'TCS', 'ALTIUZ', 'TUXPAN', 'PAD SYSTEM', 'BAC', 'PMG', 'ORANG PEOPLE SOFT', 'ANTILHUE', 'LSP', 'EXPERTI')
user_tuple =                    ('USR=', 'USER=', 'USUFTP=', 'USERFTP=') #, 'TBK4027')
ftp_tuple =                     ('OPEN', 'CD', 'LCD', 'PUT', 'QUIT', 'FTP', 'DOFTP', 'CLOSE', 'BYE', 'PWDFTP', 'HOSTFTP', 'USUFTP')

# Identificar la existencia de comandos FTP
ftp_regexp =('[^#](ftp|FTP)')

# Identificar uso del usuario
user_regexp = ('[^#](user|USER)\ {1,2}tbk4027','[^#](user|USER)\ {1,2}(\{|\'|\"|\`|\$)?[a-zA-Z0-9_]*(\{|\'|\"|\`|\$)?[a-zA-Z0-9_]*(\}|\'|\"|\`|\$)?')

# Identificar directorio local desde donde se hace el FTP
dir_local_regexp = ('[^#](lcd|LCD)\ {1,2}\${0,1}[a-zA-Z0-9_]*\/{0,1}[a-zA-Z0-9_]*') # Sino si se encuentra, se asume el directorio actual = pwd

# Identificar el archivo que se envia por FTP
put_regexp = ('[^#](put|PUT)\ {1,2}[{a-zA-Z0-9_.$"]*[a-zA-Z0-9_.$"}]*')

# Identificar el hosts al cual se hace FTP
hosts_regexp = ('[^#](host|HOST)[a-zA-Z0-9_.$]*\ {0,1}=(\'|\"|\`|\$)?[a-zA-Z0-9_.$]*(\'|\"|\`|\$)?','[^#](open|OPEN)\ {1,2}(\'|\"|\`|\$)?[a-zA-Z0-9_]*(\'|\"|\`|\$)?','[^#](ftp|FTP)\ {0,1}-(d|i|v|n)*\ -(d|i|v|n)*\ \d{2,3}\.\d{2,3}\.\d{2,3}\.\d{2,3}','[^#](ftp|FTP)\ {1,2}-(d|i|v|n)*\ -(d|i|v|n)*\ [a-zA-Z0-9_.$]*')

# Identificar directorio destino del FTP
dir_regexp = '[^#](cd|CD)\ {1,2}\${0,1}[{a-zA-Z0-9_]*\/{0,1}[}a-zA-Z0-9_]*'
# Si no se asume el directorio HOME del usuario.

# Others more
others_regexp = ('[^#]([a-zA-Z0-9_]*(ftp|FTP)[a-zA-Z0-9_]*)\ {0,1}=\ {0,1}(\'|\"|\`|\$)?[a-zA-Z0-9_]*(\'|\"|\`|\$)?')

# Function Definition Section

def remove_comments(pautaname):
        f = open(dst_directory_pautas + "/" + pautaname,"r+")
        d = f.readlines()
        f.seek(0)
        for i in d:
                if not i.startswith('#'):
                        f.write(i)
        f.truncate()
        f.close()

def clean_file(pautaname):
        all_string = str("")
        with open (dst_directory_pautas + "/" + pautaname, 'r') as file:
                for line in file:
                        if not line.startswith('#'):
                                all_string += str(line)
        #print all_string
        return all_string

def find_by_regexp(pautaname, regexp):
        response = ()
        response_list = list(response)
        # Compile regexp
        regexp_for_find = re.compile(regexp)

        remove_comments(pautaname)

        file = open (dst_directory_pautas + "/" + pautaname, 'r')
        file_text = (str(file.readlines()))

        #file_text = clean_file(pautaname)

        # Find text by regexp compiled
        for match in regexp_for_find.finditer(file_text):
                print "%s" % (match.group(0))
                response_list.append(match.group(0))
        response = set(response_list)
        return response

def find_on_dicc(dicc, filename, search_type):
        offset = 40
        file = open (dst_directory_pautas + "/" + filename, 'r')
        string_lines = (str(file.readlines())).upper()
        #print string_lines
        if search_type == 1: #Fix search
                # print "Making Fix Search.."
                # for word, index in dicc.items():
                item_found ="NOT FOUND"
                for item in dicc:
                        # print "item->" + item
                        if (string_lines.find(item) != -1):
                                item_found = item
                return item_found
        else: #Heuristic Search
                # print "Making Heuristic Search.."
                item_found ="NOT FOUND"
                for item in dicc:
                        # print "item->" + item
                        position_found = string_lines.find(item)
                        if (position_found != -1):
                                item_found = "("+str(position_found)+") " + string_lines[position_found:position_found + offset]
                return item_found

def get_ftpuser(pautaname):
        response = find_on_dicc(user_tuple, pautaname, 2)
        print "busqueda ftpuser: " + response
        return response

def get_provider(pautaname):
        print "get_provider " + pautaname
        return find_on_dicc(providers_tuple, pautaname, 1)

def get_time_pauta_hour(hour_sum, num_reg):
        response = ""
        response = str(int(round(hour_sum/num_reg))).zfill(2) # Add leading zeros
        return response

def get_time_pauta_min(min_sum, num_reg):
        response = ""
        response = str(int(round(min_sum/num_reg))).zfill(2) # Add leading zeros
        return response

def get_schedule_pauta(schedule_array):
        response = ""
        if schedule_array[0]==True:
                response += "L "
        if schedule_array[1]==True:
                response += "M "
        if schedule_array[2]==True:
                response += "M "
        if schedule_array[3]==True:
                response += "J "
        if schedule_array[4]==True:
                response += "V "
        if schedule_array[5]==True:
                response += "S "
        if schedule_array[6]==True:
                response += "D "
        return response

def get_pauta_time(pautaname):
        length_pautaname = len(pautaname)
        extract = pautaname[length_pautaname-6:length_pautaname]
        extract = extract[0:2] + ":" + extract[2:4] + ":" + extract[4:6]
        return extract

def add_file_to_output(line_exception):
        file = open(log_output_filename, "w")
        file.write(line_exception)
        file.close()
        return True

def add_file_to_exceptions(line_exception):
        file = open(pautas_exception_filename, "w")
        file.write(line_exception)
        file.close()
        return True

def add_file_to_check(line_exception):
        file = open(pautas_to_check_filename, "a+")
        file.write(line_exception + '\n')
        file.close()
        return True

def add_file_to_results(line_output):
        file = open(output_file, "a+")
        file.write(line_output + '\n')
        file.close()
        return True

def get_pauta_log_date(pautaname):
        length_pautaname = len(pautaname)
        extract=pautaname[length_pautaname-15:length_pautaname-7]
        return extract

def get_weekly_frequency(pautadate):
        # Date format received -> DDMMYYYY
        dicdias = {'MONDAY':'L','TUESDAY':'M','WEDNESDAY':'MI','THURSDAY':'J', \
        'FRIDAY':'V','SATURDAY':'S','SUNDAY':'D'}
        pautadate_length = len(pautadate)
        dia=int(pautadate[0:2])
        mes=int(pautadate[2:4])
        anio=int(pautadate[4:pautadate_length])
        fecha = datetime.date(anio, mes, dia)
        return (dicdias[fecha.strftime('%A').upper()])

def validate_pautadate(pautadate):
        if re.match('^(0[1-9]|[1-2][0-9]|31(?!(?:0[2469]|11))|30(?!02))(0[1-9]|1[0-2])([12]\d{3})$',pautadate):
                return True
        else:
                return False

def find_logs(pautaname):
        print "Looking for logs file Pauta-> " + pautaname
        try:
                index = pautaname.index('.')
        except ValueError:
                index = len(pautaname)
        pautaname_clean = pautaname[0:index]
        # print "Pauta Clean:" + pautaname_clean
        if (os.path.exists(src_directory_logs)):
                # print "LOGS directory checked OK!"
                lstDir = glob.glob(src_directory_logs +"/"+ pautaname_clean + ".log.*")
                # print lstDir
                if not lstDir:
                        print "No posee log, sera incluida la pauta en la lista para chequear!!"
                        print "=================================================================="
                        add_file_to_check(pautaname)
                else:
                        # Extract schedule & time
                        schedule_array = [False, False, False, False, False, False, False]
                        hour_sum = 0.0
                        min_sum = 0.0
                        num_reg = 0
                        line_output = ""
                        for filename in lstDir:
                                pautadate = get_pauta_log_date(filename)
                                pautatime = get_pauta_time(filename)
                                if (validate_pautadate(pautadate)):
                                        pautaweek_day = get_weekly_frequency(get_pauta_log_date(filename))
                                        if pautaweek_day =="L": # Lunes
                                                schedule_array[0]=True
                                        elif pautaweek_day =="M": # Martes
                                                schedule_array[1]=True
                                        elif pautaweek_day == "MI": # Miercoles
                                                schedule_array[2]=True
                                        elif pautaweek_day == "J": # Jueves
                                                schedule_array[3]=True
                                        elif pautaweek_day == "V": # Viernes
                                                schedule_array[4]=True
                                        elif pautaweek_day == "S": # Sabado
                                                schedule_array[5]=True
                                        elif pautaweek_day == "D": # Domingo
                                                schedule_array[6]=True
                                        # print (filename + " -> " + pautadate + " " + pautaweek_day + "\t" + pautatime)
                                        hour_sum += float(pautatime[0:2])
                                        min_sum += float(pautatime[3:5])
                                        num_reg += 1
                                else:
                                        print "Formato de Fecha invalido, sera incluida la pauta en la lista para chequear!!"
                                        print "=================================================================="
                                        add_file_to_check(pautaname)
                        if num_reg != 0:
                                # Extract schedule
                                schedule = get_schedule_pauta(schedule_array)
                                time = get_time_pauta_hour(hour_sum, num_reg) + ":" + get_time_pauta_min(min_sum, num_reg)
                                provider = get_provider(pautaname)
                                # ftpuser = get_ftpuser(pautaname)
                                ftpuser = ""
                                resultados_user = "NOT FOUND"
                                resultados_lcd = "NOT FOUND"
                                resultados_put = "NOT FOUND"
                                resultados_hosts = "NOT FOUND"
                                resultados_cd = "NOT FOUND"
                                resultados = find_by_regexp(pautaname, ftp_regexp)
                                if len(resultados) > 0: # Tiene ftp
                                        # Buscamos los usuarios de los ftp
                                        resultados = find_by_regexp(pautaname, user_regexp[0]) # Primera expresion regular sobre user
                                        if len(resultados) > 0: # Primer filtro
                                                resultados_user = ""
                                                for element in resultados:
                                                        resultados_user = resultados_user + " " + element
                                        else:
                                                # Aplicamos el segundo filtro
                                                resultados = find_by_regexp(pautaname, user_regexp[1]) # Segunda expresion regular sobre user
                                                if len(resultados) > 0: # Segundo filtro
                                                        resultados_user = ""
                                                        for element in resultados:
                                                                resultados_user = resultados_user + " " + element
                                                else:
                                                        resultados_user = "NOT FOUND"
                                                        print "Pauta no tiene TEXTO USER!!"
                                        # Buscamos el directorio local del ftp
                                        resultados = find_by_regexp(pautaname, dir_local_regexp) # Primera expresion regular sobre lcd
                                        if len(resultados) > 0: # Primer filtro
                                                resultados_lcd = ""
                                                for element in resultados:
                                                        resultados_lcd = resultados_lcd + " " + element
                                        else:
                                                resultados_lcd = "NOT FOUND"
                                                print "Pauta no tiene TEXTO LCD!!"
                                        # Buscamos el archivo a enviar por ftp
                                        resultados = find_by_regexp(pautaname, put_regexp) # Primera expresion regular sobre put
                                        if len(resultados) > 0: # Primer filtro
                                                resultados_put = ""
                                                for element in resultados:
                                                        resultados_put = resultados_put + " " + element
                                        else:
                                                resultados_put = "NOT FOUND"
                                                print "Pauta no tiene TEXTO PUT!!"

                                        # Buscamos los usuarios el hosts del hosts
                                        resultados = find_by_regexp(pautaname, hosts_regexp[0]) # Primera expresion regular sobre hosts
                                        if len(resultados) > 0: # Primer filtro
                                                resultados_hosts = ""
                                                for element in resultados:
                                                        resultados_hosts = resultados_hosts + " " + element
                                        else:
                                                # Aplicamos el segundo filtro
                                                resultados = find_by_regexp(pautaname,hosts_regexp[1]) # Segunda expresion regular sobre hosts
                                                if len(resultados) > 0: # Segundo filtro
                                                        resultados_hosts = ""
                                                        for element in resultados:
                                                                resultados_hosts = resultados_hosts + " " + element
                                                else:
                                                        # Aplicamos el tercer filtro
                                                        resultados = find_by_regexp(pautaname,hosts_regexp[2]) # Tercera expresion regular sobre hosts
                                                        if len(resultados) > 0: # Tercer filtro
                                                                resultados_hosts = ""
                                                                for element in resultados:
                                                                        resultados_hosts = resultados_hosts + " " + element
                                                        else:
                                                                # Aplicamos el cuarto filtro
                                                                resultados = find_by_regexp(pautaname,hosts_regexp[3]) # Cuarto expresion regular sobre hosts
                                                                if len(resultados) > 0: # Cuarto filtro
                                                                        resultados_hosts = ""
                                                                        for element in resultados:
                                                                                resultados_hosts = resultados_hosts + " " + element
                                                                else:
                                                                        resultados_hosts = "NOT FOUND"
                                                                        print "Pauta no tiene TEXTO HOSTS!!"
                                        # Buscamos  el directorio destino
                                        resultados = find_by_regexp(pautaname, dir_regexp) # Primera expresion regular directorio
                                        if len(resultados) > 0: # Primer filtro
                                                resultados_cd = ""
                                                for element in resultados:
                                                        resultados_cd = resultados_cd + " " + element
                                        else:
                                                resultados_cd = "NOT FOUND"
                                                print "Pauta no tiene TEXTO CD!!"
                                else:
                                        print "Pauta no tiene TEXTO FTP!!"
                                line_output = run_hostname + "&" + pautaname + "&" + schedule + time + "&" + resultados_user + "&" + resultados_lcd + "&" +resultados_put + "&" + resultados_hosts + "&" + resultados_put + "&" + resultados_user + "&" + resultados_cd  + "&" + provider
                                print line_output
                                print "=================================================================="
                                add_file_to_results(line_output)
                return True
        else:
                print "LOGS Directory does not exists!"
                return False

def copy_tmp_files():
        print "Copying temporal files..."
        if (os.path.exists(src_directory_pautas)):
                print "SRC directory checked OK!"
                if (os.path.exists(dst_directory_pautas)):
                        print "DST directory checked OK!"
                        if (os.path.exists(pautas_list_filename)):
                                line_exception=""
                                print "Pautas List File OK!"
                                # Read list file line by line
                                with open(pautas_list_filename,"r") as f:
                                        mylist = f.read().splitlines()
                                for line in mylist:
                                        try:
                                                shutil.copyfile(src_directory_pautas + "/" + line, dst_directory_pautas + "/" + line)
                                                print "Copy temp files Completed!! -> " + line
                                                find_logs(line)
                                        except IOError, e:
                                                # print e.errno
                                                print "Copy to exceptions_files.txt"
                                                line_exception = line_exception + line + "\n"
                                                print e
                                f.close()
                                add_file_to_exceptions(line_exception)
                                return True
                        else:
                                print "Pautas List File does not exists!"
                                return False
                else:
                        print "DST Directory does not exists!"
                        return False
        else:
                print "SRC Directory does not exists!"
                return False

def init():
        try:
                os.remove(output_file)
                os.remove(pautas_output_filename)
                os.remove(log_output_filename)
                os.remove(pautas_exception_filename)
                os.remove(pautas_to_check_filename)
        except OSError:
                pass

# Main Program
def main():
        print "\nWelcome to Check Pautas ***********************************"
        ask = False
        while(ask != True):
                #Ask about proceed or not
                response = raw_input("Are your sure to Check Pautas (Y/N)? ")

                if (response == "Y" or response == "y"):
                        print "Checking... "
                        ask=True
                        # Copy all file to tmp directory before do anything
                        init()
                        copy_tmp_files()
                else:
                        if (response == "N" or response == "n"):
                                print ("Bye!! ")
                                break
                        else:
                                print ("The options are (Y or N) ")

        print "\nThanks!!   ************************************************\n"

main()