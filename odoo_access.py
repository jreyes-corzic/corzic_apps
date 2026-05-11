import os

#import library to access odoo api 
import xmlrpc.client 

url=os.getenv("ODOO_URL", "https://riss-group-corzic.odoo.com")
db=os.getenv("ODOO_DB", "riss-group-corzic-main-16227912")
username=os.getenv("ODOO_USERNAME", "justin.reyes@corzic.com")
password=os.getenv("ODOO_PASSWORD")


dev_url=os.getenv("ODOO_DEV_URL", "https://riss-group-corzic-justin-staging1272026-27949620.dev.odoo.com")
dev_db=os.getenv("ODOO_DEV_DB", "riss-group-corzic-justin-staging1272026-27949620")
dev_username=os.getenv("ODOO_DEV_USERNAME", "justin.reyes@corzic.com")
dev_password=os.getenv("ODOO_DEV_PASSWORD")

models=['stock.move','stock.lot','product.template','sale.order','stock.picking','purchase.order','sale.order.line','res.partner','account.payment.term','account.fiscal.position','shipstation.instance.ept']

def access_odoo_db(url,db,uname,pw):
	if not pw:
		raise RuntimeError("ODOO_PASSWORD is required. Pass it as an environment variable.")

	common=xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(url))
	uid=common.authenticate(db,uname,pw, {})
	if not(uid):
		print("Odoo authentication failed: {}".format(uid))
		return -1
	else:
		print("Odoo authentication successful with user: {}".format(uid))
		models = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(url))
		return uid,models 

def update_id(db,uid,password,models,model,record,fields):
	return models.execute_kw(db,uid,password,model,'write',[[record],fields])
	
def get_ids(db,uid,password,models,model,conditions):
	return models.execute_kw(db,uid,password,model,'search',conditions, {})

def read_ids(db,uid,password,models,model,ids,fields):
	return models.execute_kw(db,uid,password,model,'read',[ids],{'fields':fields})
	
def create_id(db,uid,password,models,model,params):
	return models.execute_kw(db,uid,password,model,'create',[params])
	
def run_action(db,uid,password,models,model,action,record_id):
	return models.execute_kw(db,uid,password,model,action,[[record_id]])
	

