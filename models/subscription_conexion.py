from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
import psycopg2

import subprocess
import time
import logging
from sshtunnel import SSHTunnelForwarder

_logger = logging.getLogger(__name__)

class BaseDatos(models.Model):
    _name = 'base.datos.query'
    _description = 'Tabla de Bases de Datos'

    name = fields.Char(string="Nombre")
    owner = fields.Char(string="")
    tiene_subs=fields.Boolean(string="Tiene subscripcion",compute="get_subs")

    def get_subs(self):
        for line in self:
            obj=self.env["sale.subscription.line"].search([])
            if len(obj.filtered(lambda x: x.db.id==line.id))>0:
                line.tiene_subs=True
            else:
                line.tiene_subs=False
   

class Product(models.Model):
    _inherit = "sale.subscription.line"

    db=fields.Many2one("base.datos.query",string="Database")
    type_s=fields.Selection([("u","Usuarios"),("c","Compañia")],string="Tipo")

class Conection(models.Model):
    _name="conectionsubscription"

    name=fields.Char("Conf")
    host=fields.Char(string="Host")
    user=fields.Char("User")
    password=fields.Char("Password")
    port=fields.Char("Port")

    def get_conexion(self):
        ssh_host = '138.197.53.190'
        ssh_port = 22000
        ssh_user = 'databasesub'
        ssh_password = '8uJfuFX8GRHjG'

       
        obj=self.env['sale.subscription.line'].search([('type_s','=','u')])
        obj_subs=self.env['conectionsubscription'].search([("id","=",1)],limit=1)
      
        with SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(obj_subs.host , int(obj_subs.port))) as tunnel:

            for line in obj:
                try:
                    if line.db and line.type_s:
                        conexion=psycopg2.connect(host="127.0.0.1", user=obj_subs.user, port=tunnel.local_bind_port, password=obj_subs.password, database=line.db.name, sslmode="require")
                        cur=conexion.cursor()
                        cur.execute(
                            """SELECT COUNT(u.id)
                                FROM public.res_users u
                                INNER JOIN public.res_groups_users_rel g ON u.id = g.uid
                                WHERE u.active = true AND g.gid = 1;"""
                        )
                        result=cur.fetchone()
                        if result[0]-6>0:
                            line.quantity=result[0]-6
                        else:
                            line.quantity=0

                        conexion.close()
                except Exception as e:
                    _logger.info("Error" + str(e))
                    continue
           
        #ssh_client.close()



    def get_database_name(self):
        ssh_host = '138.197.53.190'
        ssh_port = 22000
        ssh_user = 'databasesub'
        ssh_password = '8uJfuFX8GRHjG'

       
      
        obj_subs=self.env['conectionsubscription'].search([("id","=",1)],limit=1)
      
        with SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(obj_subs.host , int(obj_subs.port))) as tunnel:

            
            
                
                conexion=psycopg2.connect(host="127.0.0.1", user=obj_subs.user, port=tunnel.local_bind_port, password=obj_subs.password, database="postgres", sslmode="require")
                cur=conexion.cursor()
                cur.execute(
                    """
                        SELECT datname, rolname
                        FROM pg_database
                        JOIN pg_roles ON datdba = pg_roles.oid;
                    """
                )
                result=cur.fetchall()

                resultados = [(database_name, owner_name) for database_name, owner_name in result]

                reg_existentes=self.env["base.datos.query"].search([])

                for database_name, owner_name in resultados:
                    reg_existente = reg_existentes.filtered(lambda r: r.name == database_name)
                    if reg_existente:
                        # Si el registro existe, actualiza el propietario
                        reg_existente.owner = owner_name
                    else:
                        # Si el registro no existe, crea uno nuevo
                        self.env["base.datos.query"].create({'name': database_name, 'owner': owner_name})

                # Archiva registros que no están en la lista de bases de datos
                registros_por_archivar = reg_existentes.filtered(lambda r: r.name not in [db[0] for db in resultados])
                registros_por_archivar.write({'active': False})
                

                conexion.close()
           
                

  



    

    