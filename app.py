from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

import sufs_catalog
import sufs_orders
import sufs_performance


app = Flask(__name__)


def parse_override_skus(raw_skus):
	return [
		sku.strip()
		for sku in raw_skus.replace(",", "\n").splitlines()
		if sku.strip()
	]


def create_download_zip(file_paths):
	output_dir = Path(sufs_catalog.get_output_path()).resolve()
	zip_name = f"sufs-catalog-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
	zip_path = output_dir / zip_name

	with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
		for file_path in file_paths:
			path = Path(file_path).resolve()
			if path.is_file() and output_dir in path.parents:
				archive.write(path, arcname=path.name)

	return zip_name


@app.get("/")
def index():
	return render_template("index.html")


@app.post("/generate")
def generate():
	try:
		override_skus = parse_override_skus(request.form.get("override_skus", ""))
		exports, num_removals, unknown_override_skus = sufs_catalog.get_catalog_upload(override_skus)
		files = [Path(export).name for export in exports]
		zip_file = create_download_zip(exports)
		return render_template(
			"index.html",
			files=files,
			zip_file=zip_file,
			num_removals=num_removals,
			override_skus=override_skus,
			unknown_override_skus=unknown_override_skus,
		)
	except Exception as exc:
		return render_template("index.html", error=str(exc)), 500


@app.post("/orders")
def import_orders():
	try:
		num_orders = int(request.form.get("num_orders", "10"))
		num_orders = max(1, min(num_orders, 100))
		result = sufs_orders.run_order_import(num_orders)
		return render_template("index.html", order_result=result)
	except Exception as exc:
		return render_template("index.html", order_error=str(exc)), 500


@app.get("/performance/brand-orders")
def brand_order_performance():
	try:
		uid, models = sufs_performance.get_odoo_connection()
		brands = sufs_performance.get_sufs_brand_performance(
			sufs_performance.od.db,
			uid,
			sufs_performance.od.password,
			models,
		)
		return jsonify({"brands": brands})
	except Exception as exc:
		return jsonify({"error": str(exc)}), 500


@app.get("/download/<path:filename>")
def download(filename):
	output_dir = Path(sufs_catalog.get_output_path()).resolve()
	requested_path = (output_dir / filename).resolve()

	if output_dir not in requested_path.parents or not requested_path.is_file():
		abort(404)

	return send_from_directory(output_dir, requested_path.name, as_attachment=True)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8082, debug=True)
