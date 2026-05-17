from collections import defaultdict

import odoo_access as od


START_DATE = "2025-04-01 13:47:54"


def get_odoo_connection():
	uid, models = od.access_odoo_db(od.url, od.db, od.username, od.password)
	print(f"retrieved odoo access with id: {uid}")
	return uid, models


def get_sufs_brand_order_share(db, uid, password, models):
	sufs_ids = od.get_ids(db,uid,password,models,"stock.move",[["&",("product_id.product_tmpl_id.sales_channel_ids", "in", [3]),"&",("product_brand_id", "!=", False),"&",("state", "in", ["done", "confirmed", "assigned", "partially_available"]),("x_studio_sufs_order_date", ">=", START_DATE)]])
	sufs_list = od.read_ids(db,uid,password,models,"stock.move",sufs_ids,["product_brand_id", "product_uom_qty","x_studio_sufs_price"])

	brand_totals = defaultdict(float)
	for move in sufs_list:
		brand = move.get("product_brand_id")
		if not brand:
			continue
		brand_totals[brand[1]] += float(move.get("product_uom_qty") or 0)

	total_orders = sum(brand_totals.values())
	if total_orders == 0:
		return []

	return [
		{
			"brand": brand,
			"orders": orders,
			"percentage": orders / total_orders,
		}
		for brand, orders in sorted(
			brand_totals.items(),
			key=lambda brand_total: brand_total[1],
			reverse=True,
		)
	]

def get_sufs_brand_revenue_share(db, uid, password, models):
	sufs_ids = od.get_ids(db,uid,password,models,"stock.move",[["&",("product_id.product_tmpl_id.sales_channel_ids", "in", [3]),"&",("product_brand_id", "!=", False),"&",("state", "in", ["done", "confirmed", "assigned", "partially_available"]),("x_studio_sufs_order_date", ">=", START_DATE)]])
	sufs_list = od.read_ids(db,uid,password,models,"stock.move",sufs_ids,["product_brand_id", "product_uom_qty","x_studio_sufs_price"])

	brand_totals = defaultdict(float)
	for move in sufs_list:
		brand = move.get("product_brand_id")
		if not brand:
			continue
		brand_totals[brand[1]] += float(move.get("x_studio_sufs_price") or 0)

	total_revenue = sum(brand_totals.values())
	if total_revenue == 0:
		return []

	return [
		{
			"brand": brand,
			"revenue": revenue,
			"percentage": revenue / total_revenue,
		}
		for brand, revenue in sorted(
			brand_totals.items(),
			key=lambda brand_total: brand_total[1],
			reverse=True,
		)
	]


def get_sufs_brand_revenue_share_pie_chart(db,uid,password,models,brand):
	return get_sufs_brand_revenue_share(db,uid,password,models)

def get_sufs_brand_order_share_pie_chart(db, uid, password, models):
	return get_sufs_brand_order_share(db, uid, password, models)


if __name__ == "__main__":
	uid, models = get_odoo_connection()

	for brand in get_sufs_brand_performance(od.db, uid, od.password, models):
		print(f"{brand['brand']}: {brand['percentage']:.2%}")
