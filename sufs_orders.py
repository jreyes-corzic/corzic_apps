from datetime import datetime
import json
import os
import requests
import pandas as pd
import odoo_access as od

from datetime import datetime, timedelta

# Ariba credentials and API endpoints
CLIENT_ID = os.getenv("ARIBA_CLIENT_ID")
CLIENT_SECRET = os.getenv("ARIBA_CLIENT_SECRET")
APPLICATION_KEY = os.getenv("ARIBA_APPLICATION_KEY")
TOKEN_URL = os.getenv("ARIBA_TOKEN_URL", "https://api.ariba.com/v2/oauth/token")
ORDERS_API_URL = os.getenv("ARIBA_ORDERS_API_URL", "https://openapi.ariba.com/api/purchase-orders-supplier/v1/prod")
REALM = os.getenv("ARIBA_REALM", "AN11091553062")

def get_ariba_access_token():
	if not CLIENT_ID or not CLIENT_SECRET:
		raise RuntimeError("ARIBA_CLIENT_ID and ARIBA_CLIENT_SECRET are required. Pass them as environment variables.")

	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	payload = {  
    	"grant_type": "client_credentials",  
    	"client_id": CLIENT_ID,  
    	"client_secret": CLIENT_SECRET}
	response = requests.post(TOKEN_URL, headers=headers, data=payload)
	response.raise_for_status()
	access_token=response.json()["access_token"]
	expire=datetime.now() + timedelta(minutes=30)
	return access_token,expire
	
def get_ariba_order_list_month(start_date,end_date):	
	#get access token
	access_token,expiration=get_ariba_access_token()

	
	#retrieve pending sales order data
	api_headers = { "Authorization": f"Bearer {access_token}",  
		"apiKey":APPLICATION_KEY,  
		"Accept":"application/json",
		"X-ARIBA-NETWORK-ID":REALM}
	
	all_orders=[]
	more_orders=True
	start=0
	while (more_orders):
			
		params= {"$filter" : f"startDate eq {start_date} and endDate eq {end_date}", "$top":100,"$skip":start}
		response1=requests.get(ORDERS_API_URL+"/orders",headers=api_headers,params=params)

		response1.raise_for_status()

		orders=response1.json()['content']
		all_orders.extend(orders)

		if (len(orders)<100):
			more_orders=False
		else:
			start +=100
	
	orders_df=pd.DataFrame(all_orders)
	min_revenue=0.
	for idx,row in orders_df.iterrows():
		min_revenue+=row['poAmount']['amount']
	order_list=orders_df['documentNumber'].tolist()
	return order_list,min_revenue

def get_ariba_orders_df_by_month(start_date,end_date):	
	#get access token
	access_token,expiration=get_ariba_access_token()

	
	#retrieve pending sales order data
	api_headers = { "Authorization": f"Bearer {access_token}",  
		"apiKey":APPLICATION_KEY,  
		"Accept":"application/json",
		"X-ARIBA-NETWORK-ID":REALM}
	
	all_orders=[]
	more_orders=True
	start=0
	while (more_orders):
			
		params= {"$filter" : f"startDate eq {start_date} and endDate eq {end_date}", "$top":100,"$skip":start}
		response1=requests.get(ORDERS_API_URL+"/orders",headers=api_headers,params=params)

		response1.raise_for_status()

		orders=response1.json()['content']
		all_orders.extend(orders)

		if (len(orders)<100):
			more_orders=False
		else:
			start +=100
	
	orders_df=pd.DataFrame(all_orders)
	print(orders_df.keys())
	
	return orders_df

def get_order_list_new():	
	if not APPLICATION_KEY:
		raise RuntimeError("ARIBA_APPLICATION_KEY is required. Pass it as an environment variable.")

	#get access token
	access_token,expiration=get_ariba_access_token()

	
	#retrieve pending sales order data
	api_headers = { "Authorization": f"Bearer {access_token}",  
		"apiKey":APPLICATION_KEY,  
		"Accept":"application/json",
		"X-ARIBA-NETWORK-ID":REALM}
	
	all_orders=[]
	more_orders=True
	start=0
	while (more_orders):
		params= {"$filter" : f"orderStatus eq 'New'", "$top":100,"$skip":start}
		response1=requests.get(ORDERS_API_URL+"/orders",headers=api_headers,params=params)

		response1.raise_for_status()

		orders=response1.json()['content']
		all_orders.extend(orders)

		if (len(orders)<100):
			more_orders=False
		else:
			start +=100
	
	orders_df=pd.DataFrame(all_orders)
	min_revenue=0.
	for idx,row in orders_df.iterrows():
		min_revenue+=row['poAmount']['amount']
	
	if (len(orders_df) > 0):
		order_list=orders_df['documentNumber'].tolist()
		order_date_list=orders_df['orderDate'].tolist()
		return order_list,order_date_list,min_revenue,access_token
	else:
		return [],[],min_revenue,access_token

def get_order_lines(order_list,start_date='00',end_date='00'):
	all_lines=[]
	
		
	access_token,expiration=get_ariba_access_token()

	counter=1
	for order in order_list:
		if (expiration < datetime.now()+timedelta(minutes=5)):
			print("refreshing access token...")
			access_token,expiration=get_ariba_access_token()
		
		api_headers = { "Authorization": f"Bearer {access_token}",  
			"apiKey":APPLICATION_KEY,  
			"Accept":"application/json",
			"X-ARIBA-NETWORK-ID":REALM}
		
		print(f"{counter}:Retreiving order: {order}")
		if (start_date=='00' and end_date=='00'):
			params = {"$filter": f"documentNumber eq '{str(order)}'"}
		else:
			params = {"$filter": f"documentNumber eq '{str(order)}' and startDate eq {start_date} and endDate eq {end_date}"}
		response=requests.get(ORDERS_API_URL+"/items",headers=api_headers,params=params)
		response.raise_for_status()
		lines=response.json()['content']
		all_lines.extend(lines)
		print(f"{counter}: Order {order} has {len(lines)} items")
		counter+=1
	lines_df=pd.DataFrame(all_lines)
	print(lines_df.keys())
	return lines_df


def get_order_dicts(num_orders):
	order_list,order_date_list,amount,access_token=get_order_list_new()
	if not order_list:
		return []

	order_lines=get_order_lines(order_list[0:num_orders])
	if order_lines.empty:
		return []

	order_lines=order_lines.groupby('documentNumber')
	
	
	order_dicts=[]
	ii=0
	for order,df in order_lines:
		curr_order={}
		curr_order['client_order_reference']=order
		curr_order['sufs_order']=True
		curr_order['payment_term_id']= 'Net 30'
		curr_order['partner_invoice_id']='Step Up'
		curr_order['sufs_order_date']=datetime.strptime(order_date_list[ii], "%d %b %Y %I:%M:%S %p")
		curr_order['lines']=[]
		for idx,row in df.iterrows():
			print(f"Checking order lines for {order}")
			curr_line={}
			curr_line['product_template_id']=row['supplierPart']
			curr_line['product_uom_qty']=row['quantity']
			curr_line['price_unit']=row['unitPrice']['amount']
			curr_line['purchase_price']=0.0
			curr_line['red_flag_selection']='no'
			curr_order['lines'].append(curr_line)
			
			curr_order['partner_name']=row['itemShipToName']
			curr_order['partner_id']=0
			curr_order['shipping_address']={}
			curr_order['shipping_address']['street']=row['itemShipToStreet'].split('\r\n')
			curr_order['shipping_address']['city']=row['itemShipToCity']
			curr_order['shipping_address']['zip']=row['itemShipToPostalCode']
			curr_order['shipping_address']['country']='US'
			temp=row['itemShipToCode'].split('_')
			temp=temp[1].split('-')
			curr_order['student_no']=temp[0]
			
			
		ii+=1	
		order_dicts.append(curr_order)
	#for item in order_dicts:
	#	for key,value in item.items():
	#		print(key,value)
	return order_dicts



#test order entry returns a list of dictionaries (each dictionary is a sales order to be entered)
def odoo_order_entry(num_orders):
	test=get_order_dicts(num_orders)
	created_order_ids=[]

	if not test:
		return created_order_ids

	url=od.dev_url
	db=od.dev_db
	username=od.dev_username
	password=od.dev_password
	uid,models=od.access_odoo_db(url,db,username,password)


	#retrieve plek services and shipping
	services_ids=od.get_ids(db,uid,password,models,od.models[od.models.index('product.template')],[["|",('default_code','ilike','SVC SUFS'),('default_code','=','SHIP_SHIPSTATION')]])
	services_list=od.read_ids(db,uid,password,models,od.models[od.models.index('product.template')],services_ids,['id','x_studio_product_product_id','default_code','list_price','standard_price'])
	services_df=pd.DataFrame(services_list)

	#retrieve payment term id
	payment_ids=od.get_ids(db,uid,password,models,od.models[od.models.index('account.payment.term')],[[("name", "=", "Net 30")]])
	payment_list=od.read_ids(db,uid,password,models,od.models[od.models.index('account.payment.term')],services_ids,['id'])

	#retrieve step up partner id
	sufs_id=od.get_ids(db,uid,password,models,od.models[od.models.index('res.partner')],[[("email", "ilike", "mssvendor")]])

	#retrieve ava_tax fiscal position id
	ava_tax_id=od.get_ids(db,uid,password,models,od.models[od.models.index('account.fiscal.position')],[[("name","=","Automatic Tax Mapping (AvaTax)")]])

	#retrieve ship station instance id
	ship_station_inst=od.get_ids(db,uid,password,models,od.models[od.models.index('shipstation.instance.ept')],[[("shipstation_url","=","https://ssapi.shipstation.com")]])
	for entry in test:
		#check customer
		print("\n\n")
		new_customer_flag=False
		customer_id=od.get_ids(db,uid,password,models,od.models[od.models.index('res.partner')],[[('name','ilike',entry['partner_name'])]])
		if (customer_id):
			print(f"Found customers: {customer_id}... Reading from Odoo")
			customer=od.read_ids(db,uid,password,models,od.models[od.models.index('res.partner')],customer_id,['id','name','email','street','zip','city','country_code','state_id'])
			customer_df=pd.DataFrame(customer)

			for idx,row in customer_df.iterrows():
				#verify customer by address
				#print(row['id'],row['street'],row['zip'])
				if (row['street'] in entry['shipping_address']['street'] and (entry['shipping_address']['zip'] == row['zip'] or entry['shipping_address']['zip'].split('-')[0] == row['zip'])):
					print(f'Using Odoo customer {row['id']}')
					print(f'Customer dictionary:\nname {row['name']}\nzip {row['zip']}\ncountry_code {row['country_code']}\nstate_id {row['state_id']}')
					entry['partner_id']=row['id']
			if (entry['partner_id'] == 0):
				customer_dict={}
				customer_dict['name']=entry['partner_name']
				customer_dict['street']=entry['shipping_address']['street'][0]
				customer_dict['city']=entry['shipping_address']['city']
				customer_dict['country_code']=entry['shipping_address']['country']
				customer_dict['state_id']=18
				customer_dict['country_id']=233
				customer_dict['zip']=entry['shipping_address']['zip']
				print(f"Creating new customer in Odoo...\nCustomer dictionary:")
				for key,value in customer_dict.items():
					print(key,value)
				new_customer_id=od.create_id(db,uid,password,models,od.models[od.models.index('res.partner')],[customer_dict])				
				entry['partner_id']=new_customer_id[0]
				new_customer_flag=True
		else:
			customer_dict={}
			customer_dict['name']=entry['partner_name']
			customer_dict['street']=entry['shipping_address']['street'][0]
			customer_dict['city']=entry['shipping_address']['city']
			customer_dict['country_code']=entry['shipping_address']['country']
			customer_dict['state_id']=18
			customer_dict['country_id']=233
			customer_dict['zip']=entry['shipping_address']['zip']
			print(f"Creating new customer in Odoo...\nCustomer dictionary:")
			for key,value in customer_dict.items():
				print(key,value)
			customer_id=od.create_id(db,uid,password,models,od.models[od.models.index('res.partner')],[customer_dict])				
			entry['partner_id']=customer_id[0]
			#print(f'Customer created with Odoo ID: {customer_id}')
			new_customer_flag=True	

	
		#check products on order
		order_lines=[]
		bass_flag=0
		guitar_flag=0
		mandolin_flag=0
		for prod in entry['lines']:
			product_ids=od.get_ids(db,uid,password,models,od.models[od.models.index('product.template')],[[('default_code','=',prod['product_template_id'])]])
			product_list=od.read_ids(db,uid,password,models,od.models[od.models.index('product.template')],product_ids,['id','x_studio_product_product_id','default_code','list_price','sufs_cost','standard_price','product_tag_ids'])
			product_df=pd.DataFrame(product_list)
			if (2 in product_df['product_tag_ids'].iloc[0]):
				guitar_flag+=1
				print('plek service needed')
			if (5 in product_df['product_tag_ids'].iloc[0]):
				bass_flag+=1
				print('plek service needed')
			if (4 in product_df['product_tag_ids'].iloc[0]):
				mandolin_flag+=1
				print('plek service needed')
			print(f'attaching product: {int(product_df['x_studio_product_product_id'].iloc[0])} : {prod['product_template_id']} with price {float(product_df['sufs_cost'].iloc[0])}')
			order_lines.append((0,0,{'product_id':int(product_df['x_studio_product_product_id'].iloc[0]),'product_uom_qty':prod['product_uom_qty'],'price_unit':float(product_df['sufs_cost'].iloc[0]),'red_flag_selection':prod['red_flag_selection']}))	
	
	
		#service ids - 18910 - Mandolin, 18911 - Bass, 17757 - Guitar, 30 - Ship station
		order_lines.append((0,0,{'product_id':int(services_df['x_studio_product_product_id'][3]),'product_uom_qty':1,'price_unit':0.0,'red_flag_selection':'no'}))
		
		if (guitar_flag > 0):
			order_lines.append((0,0,{'product_id':int(services_df['x_studio_product_product_id'][2]),'product_uom_qty':guitar_flag,'price_unit':75.0,'red_flag_selection':'no'}))
		if (bass_flag > 0):
			order_lines.append((0,0,{'product_id':int(services_df['x_studio_product_product_id'][1]),'product_uom_qty':bass_flag,'price_unit':95.0,'red_flag_selection':'no'}))
		if (mandolin_flag > 0):
			order_lines.append((0,0,{'product_id':int(services_df['x_studio_product_product_id'][0]),'product_uom_qty':mandolin_flag,'price_unit':55.0,'red_flag_selection':'no'}))
	
	
		#create sales order dictionary
		order_dict={
			'partner_id':entry['partner_id'],  
			'partner_invoice_id':sufs_id[0],  
			'payment_term_id':payment_ids[0],  
			'is_insurance':True,  
			'fiscal_position_id':ava_tax_id[0],  
			'is_avatax':True,  
			'is_tax_computed_externally': True,    
			'shipstation_instance_id':ship_station_inst[0],   
			'client_order_ref':entry['client_order_reference'],  
			'sufs_order':entry['sufs_order'],  
			'sufs_order_date':entry['sufs_order_date'].strftime("%Y-%m-%d %H:%M:%S"),  
			'student_no':entry['student_no'],  
			'order_line':order_lines}	
		
		for key,value in order_dict.items():
			print(key,value)
	
		order_id=od.create_id(db,uid,password,models,od.models[od.models.index('sale.order')],[order_dict])
		created_order_ids.append(order_id[0])
		print(order_id)
		print('computing taxes on order')
		action_result=od.run_action(db,uid,password,models,od.models[od.models.index('sale.order')],'button_external_tax_calculation',order_id[0])
		print(action_result)
	
		if (new_customer_flag):
			log_note='Automated sales order entry has created a new customer. Please verify the customer information. If the customer is not a duplicate, please update the customer record with phone number and email address from the SUFS program'
			try:
				models.execute_kw(db,uid,password,'sale.order','message_post',[order_id],{'body':log_note,'message_type':'comment','subtype_xmlid':'mail.mt_comment'})
			except:
				pass
		
			print(f"attached log note to sales order")

	return created_order_ids

def run_order_import(num_orders=10):
	created_order_ids=odoo_order_entry(num_orders)
	return {
		"requested_orders": num_orders,
		"created_order_ids": created_order_ids,
		"created_count": len(created_order_ids),
	}


if __name__ == "__main__":
	num_orders=10
	result=run_order_import(num_orders)
	print(f"Created {result['created_count']} sales orders.")
	for order_id in result["created_order_ids"]:
		print(order_id)
