from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource
import psycopg2
import subprocess
import time
import logging

_logger = logging.getLogger(__name__)

class Product(models.Model):
    _inherit = "sale.subscription.line"

    db=fields.Char(string="Database")
    type_s=fields.Selection([("u","Usuarios"),("c","Compañia")],string="Tipo")

class Conection(models.Model):
    _name="conectionsubscription"

    name=fields.Char("Conf")
    host=fields.Char(string="Host")
    user=fields.Char("User")
    password=fields.Char("Password")
    port=fields.Char("Port")

    def get_conexion(self):

        config_path = get_module_resource('jr_subscriptions', 'vpn', 'config.ovpn')
        command = "openvpn --config " + config_path
        try:
            # Capturamos tanto stdout como stderr
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)
            # Espera a que el proceso termine y obtén la salida y error
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"No hay conexión al VPN. Error: {stderr.decode('utf-8')}"
                raise UserError(error_msg)
            
        except Exception as e:
            raise UserError(f"Error al intentar conectar al VPN: {str(e)}")

        obj=self.env['sale.subscription.line'].search([('type_s','=','u')])
        obj_subs=self.env['conectionsubscription'].search([("id","=",1)],limit=1)
        for line in obj:
            try:
                if line.db and line.type_s:
                    conexion=psycopg2.connect(host=obj_subs.host, user=obj_subs.user, port=int(obj_subs.port), password=obj_subs.password, database=line.db, sslmode="require")
                    cur=conexion.cursor()
                    cur.execute(
                        """SELECT COUNT(u.id)
                            FROM public.res_users u
                            INNER JOIN public.res_groups_users_rel g ON u.id = g.uid
                            WHERE u.active = true AND g.gid = 1;"""
                    )
                    result=cur.fetchone()
                    line.quantity=result[0]-6

                    conexion.close()
            except Exception as e:
                _logger.info("Error" + str(e))
                continue
        time.sleep(5)
        process.terminate()



    


  



    

    