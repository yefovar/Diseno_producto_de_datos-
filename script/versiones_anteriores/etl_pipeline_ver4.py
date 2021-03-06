# config: utf8
import json, os, datetime, boto3, luigi, requests
import luigi.contrib.s3
from luigi.contrib.postgres import CopyToTable, PostgresQuery
from luigi.mock import MockTarget
from luigi.contrib import rdbms
#from luigi.postgres import PostgresQuery
#from luigi.contrib.external_program import ExternalProgramTask
#import luigi.mock
#import requests
import pandas as pd
import getpass
#import socket   #para ip de metadatos
import funciones_rds
import funciones_s3
import funciones_req



class CreaInstanciaRDS(luigi.Task):
    """ Crea la insancia en RDS cuando se tiene el Subnet Group"""
    
    db_instance_id = luigi.Parameter()
    db_name = luigi.Parameter()
    db_user_name = luigi.Parameter()
    db_user_password = luigi.Parameter()
    subnet_group = luigi.Parameter()
    security_group = luigi.Parameter()
    
    def run(self):
        exito = funciones_rds.create_db_instance(self.db_instance_id, self.db_name, self.db_user_name, 
                                         self.db_user_password, self.subnet_group, self.security_group)
        if exito ==1:
            with self.output().open('w') as out:
                out.write('RDS creada, ' + str(datetime.datetime.now()))

    def output(self):
        return luigi.LocalTarget('1.instanciaRDS.txt')
    



class CreaEsquemaRAW(PostgresQuery):

    #Para la creacion de la base
    db_instance_id = luigi.Parameter()
    subnet_group = luigi.Parameter()
    security_group = luigi.Parameter()

    #Para conectarse a la base
    host = luigi.Parameter()
    database = luigi.Parameter()
    user = luigi.Parameter()
    password = luigi.Parameter()

    table = ""
    query = "DROP SCHEMA IF EXISTS raw cascade; CREATE SCHEMA raw;"

    def requires(self):
        return CreaInstanciaRDS(self.db_instance_id, self.database, self.user,
                                self.password, self.subnet_group, self.security_group)
    



    
class CreaTablaRawJson(PostgresQuery):

    #Para la creacion de la base
    db_instance_id = luigi.Parameter()
    subnet_group = luigi.Parameter()
    security_group = luigi.Parameter()

    #Para conectarse a la base
    host = luigi.Parameter()
    database = luigi.Parameter()
    user = luigi.Parameter()
    password = luigi.Parameter()

    table = ""
    query = "CREATE TABLE raw.IncidentesVialesJson(registros JSON NOT NULL);"

    def requires(self):
         return CreaEsquemaRAW(self.db_instance_id, self.subnet_group, self.security_group,
                               self.host, self.database, self.user, self.password)

    


class CreaTablaRawMetadatos(PostgresQuery):

    #Para la creacion de la base
    db_instance_id = luigi.Parameter()
    subnet_group = luigi.Parameter()
    security_group = luigi.Parameter()

    #Para conectarse a la base
    host = luigi.Parameter()
    database = luigi.Parameter()
    user = luigi.Parameter()
    password = luigi.Parameter()

    table = ""

    query = "CREATE TABLE raw.Metadatos(dataset VARCHAR, timezone VARCHAR, rows INT, refine_ano VARCHAR, refine_mes VARCHAR, parametro_url VARCHAR, fecha_ejecucion VARCHAR, ip_address VARCHAR, usuario VARCHAR, nombre_archivo VARCHAR, formato_archivo VARCHAR ); "

 
    def requires(self):
        return  CreaTablaRawJson(self.db_instance_id, self.subnet_group, self.security_group,
                                 self.host, self.database, self.user, self.password),
    





class ExtraeInfoPrimeraVez(luigi.Task):
    """
    Extrae toda la informacion: desde el inicio (1-Ene-2014) hasta 2 meses antes de la fecha actual
    """
    #Para la creacion de la base
    db_instance_id = luigi.Parameter()
    db_name = luigi.Parameter()
    db_user_name = luigi.Parameter()
    db_user_password = luigi.Parameter()
    subnet_group = luigi.Parameter()
    security_group = luigi.Parameter()
    host = luigi.Parameter()

    #Ruta de la API
    data_url =   "https://datos.cdmx.gob.mx/api/records/1.0/download/?dataset=incidentes-viales-c5"
    meta_url =   "https://datos.cdmx.gob.mx/api/records/1.0/search/?dataset=incidentes-viales-c5"

    #Parametros de fechas
    year = 0
    month = 0
    
            
    def requires(self):
        print("...en ExtraeInfoPrimeraVez...")
        # Indica que se debe hacer primero las tareas especificadas aqui
        return  CreaTablaRawMetadatos(self.db_instance_id, self.subnet_group, self.security_group,
                                      self.host, self.db_name, self.db_user_name, self.db_user_password)


    def run(self):
        #Parametros de los datos
        #DATE_START = datetime.date(2014,1,1)
        DATE_START = datetime.date(2020,1,1)
        date_today = datetime.date.today()
        date_end = datetime.date(date_today.year, date_today.month - 2, 1)

        #periodo de fechas mensuales
        dates = pd.period_range(start=str(DATE_START), end=str(date_end), freq='M')

        for date in dates:
            self.year = date.year
            self.month = date.month
            

            #hacemos el requerimiento para un chunk del los registros
            [records, metadata] = funciones_req.peticion_api_info_mensual(self.data_url, self.meta_url, self.month, self.year)
            db_endpoint = funciones_rds.db_endpoint(self.db_instance_id)
            funciones_rds.bulkInsert([(json.dumps(records[i]['fields']) , ) for i in range(0, len(records))], [funciones_req.crea_rows_para_metadata(metadata)] , self.db_name, self.db_user_name, self.db_user_password, db_endpoint)

            #Archivo para que Luigi sepa que ya realizo la tarea
            with self.output().open('w') as out:
                out.write('Archivo: ' + str(self.year) + ' ' + str(self.month) + '\n')
 
    def output(self):
        return luigi.LocalTarget('2.insertarDB.txt')






class AcomodaBase(PostgresQuery):

    #Para la creacion de la base
    db_instance_id = 'db-dpa20'
    db_name = 'db_accidentes_cdmx'
    db_user_name = 'postgres'
    db_user_password = 'passwordDB'
    subnet_group = 'subnet_gp_dpa20'
    security_group = 'sg-09b7d6fd6a0daf19a'

    host = funciones_rds.db_endpoint(db_instance_id)
    database = db_name
    user = db_user_name
    password = db_user_password
    table = ""
#    query = "INSERT INTO raw.test SELECT properties -> 'latitud', properties -> 'delegacion_inicio', properties -> 'folio' from raw.incidentesvialesjson limit 10; "
    query = "CREATE TABLE raw.test2(latitud varchar, delegacion_inicio varchar, folio varchar);"

    def requires(self):
         return ExtraeInfoPrimeraVez(self.db_instance_id, self.db_name, self.db_user_name,
                                     self.db_user_password, self.subnet_group, self.security_group, self.host)

      
